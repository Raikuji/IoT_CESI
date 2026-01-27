from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security config
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Role definitions for IoT Campus context
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

# In-memory user storage (replace with database in production)
users_db = {
    "theo.pellizzari@viacesi.fr": {
        "id": 1,
        "email": "theo.pellizzari@viacesi.fr",
        "first_name": "Theo",
        "last_name": "Pellizzari",
        "hashed_password": pwd_context.hash("admin123"),
        "role": "admin",
        "department": "Informatique",
        "avatar_color": "#ef4444",
        "created_at": datetime.utcnow().isoformat(),
        "last_login": datetime.utcnow().isoformat(),
        "is_active": True
    }
}
user_id_counter = 2


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


def get_user_by_email(email: str) -> Optional[dict]:
    return users_db.get(email)


def get_random_color() -> str:
    import random
    colors = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6", "#ec4899", "#06b6d4"]
    return random.choice(colors)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
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
    
    user = get_user_by_email(email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def user_to_response(user: dict) -> UserResponse:
    role = user.get("role", "user")
    return UserResponse(
        id=user["id"],
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        role=role,
        role_info=ROLES.get(role, ROLES["user"]),
        department=user.get("department", "CESI Nancy"),
        avatar_color=user.get("avatar_color", "#3b82f6"),
        created_at=user["created_at"],
        last_login=user.get("last_login"),
        is_active=user.get("is_active", True)
    )


# Routes
@router.get("/roles")
async def get_roles():
    """Get all available roles"""
    return ROLES


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    global user_id_counter
    
    if get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Determine role (admin for specific emails)
    role = "admin" if user_data.email == "theo.pellizzari@viacesi.fr" else "user"
    
    new_user = {
        "id": user_id_counter,
        "email": user_data.email,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "hashed_password": get_password_hash(user_data.password),
        "role": role,
        "department": user_data.department or "CESI Nancy",
        "avatar_color": get_random_color(),
        "created_at": datetime.utcnow().isoformat(),
        "last_login": datetime.utcnow().isoformat(),
        "is_active": True
    }
    
    users_db[user_data.email] = new_user
    user_id_counter += 1
    
    access_token = create_access_token(data={"sub": user_data.email})
    
    return TokenResponse(
        access_token=access_token,
        user=user_to_response(new_user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    user = get_user_by_email(user_data.email)
    
    if not user or not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé. Contactez un administrateur."
        )
    
    # Update last login
    user["last_login"] = datetime.utcnow().isoformat()
    
    access_token = create_access_token(data={"sub": user["email"]})
    
    return TokenResponse(
        access_token=access_token,
        user=user_to_response(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return user_to_response(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    user = users_db.get(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if data.first_name:
        user["first_name"] = data.first_name
    if data.last_name:
        user["last_name"] = data.last_name
    if data.department:
        user["department"] = data.department
    if data.avatar_color:
        user["avatar_color"] = data.avatar_color
    
    return user_to_response(user)


@router.put("/password")
async def change_password(
    data: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    user = users_db.get(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(data.current_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    
    # Update password
    user["hashed_password"] = get_password_hash(data.new_password)
    
    return {"success": True, "message": "Mot de passe modifié avec succès"}


# Admin routes
@router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(get_current_admin)):
    return [user_to_response(u) for u in users_db.values()]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user: dict = Depends(get_current_admin)):
    for user in users_db.values():
        if user["id"] == user_id:
            return user_to_response(user)
    raise HTTPException(status_code=404, detail="User not found")


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: dict = Depends(get_current_admin)
):
    target_user = None
    for user in users_db.values():
        if user["id"] == user_id:
            target_user = user
            break
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if data.first_name is not None:
        target_user["first_name"] = data.first_name
    if data.last_name is not None:
        target_user["last_name"] = data.last_name
    if data.department is not None:
        target_user["department"] = data.department
    if data.is_active is not None:
        if target_user["email"] == current_user["email"]:
            raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
        target_user["is_active"] = data.is_active
    
    return user_to_response(target_user)


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_data: RoleUpdate,
    current_user: dict = Depends(get_current_admin)
):
    target_user = None
    for user in users_db.values():
        if user["id"] == user_id:
            target_user = user
            break
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user["email"] == current_user["email"]:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    if role_data.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {list(ROLES.keys())}")
    
    target_user["role"] = role_data.role
    return {"success": True, "user": user_to_response(target_user)}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_admin)
):
    target_email = None
    for email, user in users_db.items():
        if user["id"] == user_id:
            target_email = email
            break
    
    if not target_email:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_email == current_user["email"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    del users_db[target_email]
    return {"success": True}


# Stats endpoint for admin dashboard
@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_admin)):
    users = list(users_db.values())
    
    role_counts = {}
    for role in ROLES:
        role_counts[role] = len([u for u in users if u.get("role") == role])
    
    active_count = len([u for u in users if u.get("is_active", True)])
    inactive_count = len(users) - active_count
    
    # Recent activity (last 24h logins)
    now = datetime.utcnow()
    recent_logins = []
    for u in users:
        if u.get("last_login"):
            try:
                last_login = datetime.fromisoformat(u["last_login"])
                if (now - last_login).total_seconds() < 86400:
                    recent_logins.append(user_to_response(u))
            except:
                pass
    
    return {
        "total_users": len(users),
        "active_users": active_count,
        "inactive_users": inactive_count,
        "role_distribution": role_counts,
        "recent_logins": recent_logins,
        "roles": ROLES
    }
