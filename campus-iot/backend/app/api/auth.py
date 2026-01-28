"""
Authentication API - Connected to Supabase PostgreSQL
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
import os
import random

from db.database import get_db
from models.user import User, ActivityLog

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security config
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Role definitions
ROLES = {
    "admin": {
        "name": "Administrateur",
        "description": "Accès complet au système",
        "color": "#ef4444",
        "icon": "mdi-shield-crown",
        "permissions": ["all"]
    },
    "technician": {
        "name": "Technicien",
        "description": "Gestion des capteurs et maintenance",
        "color": "#f59e0b",
        "icon": "mdi-wrench",
        "permissions": ["sensors", "actuators", "alerts", "building", "control"]
    },
    "manager": {
        "name": "Responsable",
        "description": "Supervision et rapports",
        "color": "#8b5cf6",
        "icon": "mdi-account-tie",
        "permissions": ["dashboard", "sensors", "alerts", "building", "reports"]
    },
    "user": {
        "name": "Utilisateur",
        "description": "Consultation uniquement",
        "color": "#3b82f6",
        "icon": "mdi-account",
        "permissions": ["dashboard", "sensors", "alerts"]
    },
    "guest": {
        "name": "Invité",
        "description": "Accès limité en lecture",
        "color": "#6b7280",
        "icon": "mdi-account-outline",
        "permissions": ["dashboard"]
    }
}


# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    department: Optional[str] = "CESI Nancy"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    role_info: dict
    department: str
    avatar_color: str
    created_at: str
    last_login: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RoleUpdate(BaseModel):
    role: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    avatar_color: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_random_color() -> str:
    colors = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6", "#ec4899", "#06b6d4"]
    return random.choice(colors)


def user_to_response(user: User) -> UserResponse:
    role = user.role or "user"
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        role=role,
        role_info=ROLES.get(role, ROLES["user"]),
        department=user.department or "CESI Nancy",
        avatar_color=user.avatar_color or "#3b82f6",
        created_at=user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat(),
        last_login=user.last_login.isoformat() if user.last_login else None,
        is_active=user.is_active if user.is_active is not None else True
    )


def log_activity(db: Session, user_id: int, user_email: str, action: str, details: str = None, ip: str = None):
    """Log user activity to database"""
    try:
        log = ActivityLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            details=details,
            ip_address=ip
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"Failed to log activity: {e}")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Routes
@router.get("/roles")
async def get_roles():
    """Get all available roles"""
    return ROLES


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    # Check if email exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Determine role (admin for specific emails)
    role = "admin" if user_data.email == "theo.pellizzari@viacesi.fr" else "user"
    
    # Create user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=role,
        department=user_data.department or "CESI Nancy",
        avatar_color=get_random_color(),
        is_active=True,
        last_login=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log activity
    client_ip = request.client.host if request.client else None
    log_activity(db, new_user.id, new_user.email, "register", "New user registration", client_ip)
    
    access_token = create_access_token(data={"sub": user_data.email})
    
    return TokenResponse(
        access_token=access_token,
        user=user_to_response(new_user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé. Contactez un administrateur."
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Log activity
    client_ip = request.client.host if request.client else None
    log_activity(db, user.id, user.email, "login", "User login", client_ip)
    
    access_token = create_access_token(data={"sub": user.email})
    
    return TokenResponse(
        access_token=access_token,
        user=user_to_response(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return user_to_response(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.first_name:
        current_user.first_name = data.first_name
    if data.last_name:
        current_user.last_name = data.last_name
    if data.department:
        current_user.department = data.department
    if data.avatar_color:
        current_user.avatar_color = data.avatar_color
    
    db.commit()
    db.refresh(current_user)
    
    log_activity(db, current_user.id, current_user.email, "profile_update", "Profile updated")
    
    return user_to_response(current_user)


@router.put("/password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify current password
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    
    # Update password
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    
    log_activity(db, current_user.id, current_user.email, "password_change", "Password changed")
    
    return {"success": True, "message": "Mot de passe modifié avec succès"}


# Admin routes
@router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [user_to_response(u) for u in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_response(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if data.first_name is not None:
        target_user.first_name = data.first_name
    if data.last_name is not None:
        target_user.last_name = data.last_name
    if data.department is not None:
        target_user.department = data.department
    if data.is_active is not None:
        if target_user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
        target_user.is_active = data.is_active
    
    db.commit()
    db.refresh(target_user)
    
    log_activity(db, current_user.id, current_user.email, "admin_update_user", f"Updated user {target_user.email}")
    
    return user_to_response(target_user)


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    if role_data.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {list(ROLES.keys())}")
    
    target_user.role = role_data.role
    db.commit()
    db.refresh(target_user)
    
    log_activity(db, current_user.id, current_user.email, "admin_change_role", f"Changed {target_user.email} role to {role_data.role}")
    
    return {"success": True, "user": user_to_response(target_user)}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    email = target_user.email
    db.delete(target_user)
    db.commit()
    
    log_activity(db, current_user.id, current_user.email, "admin_delete_user", f"Deleted user {email}")
    
    return {"success": True}


# Stats endpoint for admin dashboard
@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    
    role_counts = {}
    for role in ROLES:
        role_counts[role] = len([u for u in users if u.role == role])
    
    active_count = len([u for u in users if u.is_active])
    inactive_count = len(users) - active_count
    
    # Recent activity (last 24h logins)
    now = datetime.utcnow()
    recent_logins = []
    for u in users:
        if u.last_login:
            try:
                # Handle timezone-aware datetimes from PostgreSQL
                last_login = u.last_login.replace(tzinfo=None) if u.last_login.tzinfo else u.last_login
                if (now - last_login).total_seconds() < 86400:
                    recent_logins.append(user_to_response(u))
            except Exception:
                pass
    
    return {
        "total_users": len(users),
        "active_users": active_count,
        "inactive_users": inactive_count,
        "role_distribution": role_counts,
        "recent_logins": recent_logins,
        "roles": ROLES
    }
