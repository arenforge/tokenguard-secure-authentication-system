"""
Role-Based Access Control (RBAC)
Simple implementation for managing user roles and permissions
"""
from enum import Enum
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer, ForeignKey
from database import Base, SessionLocal, User
from jwt_auth import get_current_user

# Add role column to User model (in a real app, this would be in database.py)
# For simplicity, we'll use a role field

class Role(str, Enum):
    """User roles"""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_role(allowed_roles: list[Role]):
    """Dependency to check if user has required role"""
    def role_checker(current_user: User = Depends(get_current_user)):
        # Simple role check - in production, add 'role' column to User table
        # For now, we'll use a simple check based on user ID or email
        user_role = get_user_role(current_user)
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

def get_user_role(user: User) -> Role:
    """Get user role from database"""
    try:
        return Role(user.role)
    except ValueError:
        return Role.USER

def assign_role(user_id: int, role: Role, db: Session):
    """Assign role to user in database"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role.value
    db.commit()
    db.refresh(user)
    return {"message": f"Role {role.value} assigned to user {user_id}"}

def check_permission(user: User, permission: str) -> bool:
    """Check if user has specific permission"""
    role = get_user_role(user)
    
    # Simple permission mapping
    permissions = {
        Role.ADMIN: ["read", "write", "delete", "admin"],
        Role.MODERATOR: ["read", "write"],
        Role.USER: ["read"]
    }
    
    return permission in permissions.get(role, [])

def require_permission(permission: str):
    """Dependency to check if user has required permission"""
    def permission_checker(current_user: User = Depends(get_current_user)):
        if not check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker

