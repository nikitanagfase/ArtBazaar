"""
routers/users.py  –  Authentication, registration, and profile endpoints.
"""

import os
import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from database import get_db
import models, schemas
from auth import (
    hash_password, verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth & users"])

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads")) / "avatars"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ── Register ───────────────────────────────────────────────────────────────

@router.post("/register", response_model=schemas.TokenOut, status_code=201)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(400, "Email already registered")

    user = models.User(
        full_name       = payload.full_name,
        email           = payload.email,
        hashed_password = hash_password(payload.password),
        role            = payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"access_token": token, "token_type": "bearer", "user": user}


# ── Login ──────────────────────────────────────────────────────────────────

@router.post("/login", response_model=schemas.TokenOut)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account is deactivated")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"access_token": token, "token_type": "bearer", "user": user}


# ── Profile ────────────────────────────────────────────────────────────────

@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=schemas.UserOut)
def update_me(
    payload: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/avatar", response_model=schemas.UserOut)
def upload_avatar(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(400, "Only JPG/PNG/WEBP files accepted")

    filename = f"{current_user.id}_{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    current_user.avatar_url = f"/static/avatars/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user


# ── Public artist profile ──────────────────────────────────────────────────

@router.get("/artist/{artist_id}", response_model=schemas.UserOut)
def get_artist_profile(artist_id: int, db: Session = Depends(get_db)):
    artist = (
        db.query(models.User)
        .filter(models.User.id == artist_id, models.User.role == models.UserRole.artist)
        .first()
    )
    if not artist:
        raise HTTPException(404, "Artist not found")
    return artist


# ── Notifications ──────────────────────────────────────────────────────────

@router.get("/me/notifications", response_model=list[schemas.NotificationOut])
def get_notifications(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id)
        .order_by(models.Notification.created_at.desc())
        .limit(50)
        .all()
    )


@router.put("/me/notifications/{notif_id}/read")
def mark_read(
    notif_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notif = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notif_id,
            models.Notification.user_id == current_user.id,
        )
        .first()
    )
    if not notif:
        raise HTTPException(404, "Notification not found")
    notif.is_read = True
    db.commit()
    return {"detail": "marked as read"}

    # ── All Artists (public) ───────────────────────────────────────────────────

@router.get("/artists", response_model=list[schemas.UserOut])
def get_all_artists(db: Session = Depends(get_db)):
    artists = (
        db.query(models.User)
        .filter(
            models.User.role == models.UserRole.artist,
            models.User.is_active == True,
        )
        .order_by(models.User.created_at.desc())
        .all()
    )
    return artists
