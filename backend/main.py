from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import os
import httpx
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from passlib.context import CryptContext
from database import SessionLocal, engine, Base, User
from jwt_auth import create_access_token, authenticate_user, get_current_user
from rbac import Role, get_user_role, require_role, require_permission, check_permission

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# create DB tables if not present
Base.metadata.create_all(bind=engine)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="User Auth & Profiles", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models (schemas)
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    class Config:
        from_attributes = True

class RoleUpdate(BaseModel):
    role: str

@app.post("/register", response_model=dict, tags=["Auth"])
def register(payload: UserCreate, db: Session = Depends(get_db)):
    # simple unique email check
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = pwd_context.hash(payload.password)
    user = User(name=payload.name, email=payload.email, password=hashed, role="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Registered", "user_id": user.id}

@app.post("/login", response_model=dict, tags=["Auth"])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint that returns JWT token"""
    user = authenticate_user(payload.email, payload.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user.email})
    user_role = get_user_role(user)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "role": user_role.value,
        "message": "Login successful"
    }

# --- OAUTH ENDPOINTS ---
@app.get("/auth/google/login", tags=["OAuth"])
def google_login():
    url = f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
    return RedirectResponse(url)

@app.get("/auth/google/callback", tags=["OAuth"])
async def google_callback(code: str, db: Session = Depends(get_db)):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        access_token = response.json().get("access_token")
        
        user_info = await client.get("https://www.googleapis.com/oauth2/v1/userinfo", headers={"Authorization": f"Bearer {access_token}"})
        user_data = user_info.json()
        
    email = user_data.get("email")
    name = user_data.get("name")
    
    if not email:
        raise HTTPException(status_code=400, detail="Failed to get email from Google")
        
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(name=name, email=email, password="", role="user")
        db.add(user)
        db.commit()
        db.refresh(user)
        
    token = create_access_token(data={"sub": user.email})
    role = get_user_role(user)
    
    return RedirectResponse(f"{FRONTEND_URL}?token={token}&email={user.email}&role={role.value}&id={user.id}")
# -----------------------

@app.get("/users", response_model=list[UserOut], tags=["Users"])
def list_users(current_user: User = Depends(require_permission("read")), db: Session = Depends(get_db)):
    """Get all users - requires authentication and read permission"""
    return db.query(User).all()

@app.get("/users/{user_id}", response_model=UserOut, tags=["Users"])
def get_user(user_id: int, current_user: User = Depends(require_permission("read")), db: Session = Depends(get_db)):
    """Get user by ID - requires authentication and read permission"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=dict, tags=["Users"])
def update_user(user_id: int, payload: UserCreate, current_user: User = Depends(require_permission("write")), db: Session = Depends(get_db)):
    """Update user - requires write permission (admin or moderator only)"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.name = payload.name
    user.email = payload.email
    user.password = pwd_context.hash(payload.password)
    db.add(user)
    db.commit()
    return {"message": "Updated"}

@app.delete("/users/{user_id}", response_model=dict, tags=["Users"])
def delete_user(user_id: int, current_user: User = Depends(require_permission("delete")), db: Session = Depends(get_db)):
    """Delete user - requires delete permission (admin only)"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "Deleted"}

@app.patch("/users/{user_id}/role", response_model=dict, tags=["Users"])
def update_user_role(
    user_id: int,
    payload: RoleUpdate,
    current_user: User = Depends(require_role([Role.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update a user's role - Admin only. Valid roles: user, moderator, admin"""
    valid_roles = [r.value for r in Role]
    if payload.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Admins cannot change their own role")
    user.role = payload.role
    db.commit()
    return {"message": f"Role updated to '{payload.role}' for user {user_id}"}

# RBAC Demo Endpoints (requires JWT authentication)

@app.get("/admin-only", tags=["RBAC Demo"])
def admin_only_endpoint(current_user: User = Depends(require_role([Role.ADMIN]))):
    """Only accessible by admin users"""
    return {"message": "Admin access granted", "user": current_user.email}

@app.get("/moderator-or-admin", tags=["RBAC Demo"])
def moderator_endpoint(current_user: User = Depends(require_role([Role.ADMIN, Role.MODERATOR]))):
    """Accessible by admin or moderator users"""
    return {"message": "Moderator/Admin access granted", "user": current_user.email}

@app.get("/check-permission/{permission}", tags=["RBAC Demo"])
def check_user_permission(permission: str, current_user: User = Depends(require_permission("read"))):
    """Check if user has a specific permission"""
    has_permission = check_permission(current_user, permission)
    user_role = get_user_role(current_user)
    return {
        "user": current_user.email,
        "role": user_role.value,
        "permission": permission,
        "has_permission": has_permission
    }
