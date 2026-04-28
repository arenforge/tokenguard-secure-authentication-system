# 🚀 TokenGuard – Secure Authentication & User Management System

> A FastAPI-powered authentication system with JWT, RBAC, and a vanilla JavaScript frontend.

---

## 🌐 Live Demo

🔗 Frontend: [https://tokenguard-secure-authentication-sy.vercel.app/](https://tokenguard-secure-authentication-sy.vercel.app/)

🔗 Backend API: [https://tokenguard-secure-authentication-system-production.up.railway.app](https://tokenguard-secure-authentication-system-production.up.railway.app)

---

## 📌 Overview

**TokenGuard** is a lightweight authentication system designed for secure user management and role-based access.

* 🔐 JWT-based authentication
* 👥 Role-Based Access Control (Admin / Moderator / User)
* ⚡ FastAPI backend with auto-generated API docs
* 🎨 Clean frontend with complete auth flow

---

## ✨ Features

### 🔐 Authentication

* User registration & login
* Secure password hashing (bcrypt)
* JWT token generation & validation

### 👥 Authorization

* **Admin** → Full access
* **Moderator** → Read & update
* **User** → Read-only

### 👤 User Management

* Get all users
* Get user by ID
* Update user
* Delete user (admin only)

---

## 🏗️ Tech Stack

| Layer      | Tech                                 |
| ---------- | ------------------------------------ |
| Backend    | FastAPI (Python)                     |
| Auth       | JWT, bcrypt                          |
| Database   | SQLite                               |
| Frontend   | HTML, CSS, JavaScript                |
| Deployment | Railway (Backend), Vercel (Frontend) |

---

## 📂 Project Structure

```
.
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── jwt_auth.py
│   ├── rbac.py
│   ├── requirements.txt
│   └── users.db
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── config.js
│
├── DEPLOYMENT.md
└── README.md
```

---

## ⚙️ Local Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

cd backend
uvicorn main:app --reload
```

👉 [http://localhost:8000](http://localhost:8000)

```bash
cd frontend
python -m http.server 3000
```

👉 [http://localhost:3000](http://localhost:3000)

---

## 📖 API Docs

* Swagger → [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc → [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔌 API Endpoints

### Auth

* `POST /register`
* `POST /login`

### Users

* `GET /users`
* `GET /users/{id}`
* `PUT /users/{id}`
* `DELETE /users/{id}`

---

## 🚀 Deployment

### Backend

```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Frontend

```js
API_URL = "https://tokenguard-secure-authentication-system-production.up.railway.app"
```

---

## 👨‍💻 Authors

* **Arhan Khan**


---

## ⭐ Support

If you found this useful, consider giving it a ⭐ on GitHub.
