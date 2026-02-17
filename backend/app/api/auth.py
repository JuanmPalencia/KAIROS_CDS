from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import timedelta, datetime

from ..storage.db import get_db
from ..storage.models_sql import User
from ..auth.security import verify_password, get_password_hash, create_access_token
from ..auth.dependencies import get_current_user, require_role
from ..config import ACCESS_TOKEN_EXPIRE_MINUTES
from ..storage.repos.audit_repo import AuditRepo
from ..core.cybersecurity import (
    record_login_failure,
    record_login_success,
    is_brute_force_locked,
    register_session,
    revoke_session,
    validate_password,
    _emit_event,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = "VIEWER"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint to get access token"""
    ip = request.client.host if request.client else "0.0.0.0"

    # Brute-force lockout check
    locked, remaining = is_brute_force_locked(ip)
    if locked:
        raise HTTPException(
            status_code=429,
            detail=f"IP bloqueada temporalmente. Espera {remaining}s.",
        )

    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        record_login_failure(ip, form_data.username)
        _emit_event("LOGIN_FAILURE", "MEDIUM", ip, f"Login fallido para user '{form_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Success — clear brute-force record
    record_login_success(ip)
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    # Register active session
    register_session(access_token, user.username, ip)
    
    # Audit log
    AuditRepo.log(
        db=db,
        action="LOGIN",
        user_id=user.id,
        username=user.username,
        ip_address=ip,
    )
    _emit_event("LOGIN_SUCCESS", "LOW", ip, f"Login exitoso: {user.username} ({user.role})")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Register a new user (Admin only)"""
    # Password policy check
    pwd_ok, pwd_err = validate_password(user_data.password)
    if not pwd_ok:
        raise HTTPException(status_code=400, detail=f"Contraseña inválida: {pwd_err}")
    
    # Check if user exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Audit log
    AuditRepo.log(
        db=db,
        action="CREATE",
        resource="USER",
        resource_id=str(user.id),
        user_id=current_user.id,
        username=current_user.username,
        details=f"Created user {user.username} with role {user.role}"
    )
    
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user


@router.post("/init-admin")
async def init_admin(db: Session = Depends(get_db)):
    """Initialize default admin user (ONLY if no users exist)"""
    if db.query(User).count() > 0:
        raise HTTPException(status_code=400, detail="Users already exist")
    
    # Create default admin
    admin = User(
        username="admin",
        email="admin@kairos.local",
        full_name="System Administrator",
        hashed_password=get_password_hash("admin123"),
        role="ADMIN",
        is_active=True
    )
    db.add(admin)
    
    # Create default operator
    operator = User(
        username="operator",
        email="operator@kairos.local",
        full_name="Central Dispatcher",
        hashed_password=get_password_hash("operator123"),
        role="OPERATOR",
        is_active=True
    )
    db.add(operator)

    # Create default doctor
    doctor = User(
        username="doctor",
        email="doctor@kairos.local",
        full_name="Dr. Elena Martínez",
        hashed_password=get_password_hash("doctor123"),
        role="DOCTOR",
        is_active=True
    )
    db.add(doctor)

    # Create default viewer
    viewer = User(
        username="viewer",
        email="viewer@kairos.local",
        full_name="Demo Viewer",
        hashed_password=get_password_hash("viewer123"),
        role="VIEWER",
        is_active=True
    )
    db.add(viewer)
    
    db.commit()

    _emit_event("ADMIN_INIT", "HIGH", "system", "Default users initialized via init-admin")
    
    return {
        "message": "Default users created. Cambia las contraseñas inmediatamente.",
        "users": [
            {"username": "admin", "role": "ADMIN"},
            {"username": "operator", "role": "OPERATOR"},
            {"username": "doctor", "role": "DOCTOR"},
            {"username": "viewer", "role": "VIEWER"}
        ]
    }
