"""
routers/custom_orders.py  –  Commission / custom artwork request endpoints.
"""

import os, uuid, shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
import models, schemas
from auth import get_current_user, get_current_artist

router = APIRouter(prefix="/api/custom-orders", tags=["custom orders"])

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads")) / "reference"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ── Buyer: create request ──────────────────────────────────────────────────

@router.post("", response_model=schemas.CustomOrderOut, status_code=201)
def create_custom_order(
    payload:      schemas.CustomOrderCreate,
    current_user: models.User = Depends(get_current_user),
    db:           Session     = Depends(get_db),
):
    artist = db.query(models.User).filter(
        models.User.id == payload.artist_id,
        models.User.role == models.UserRole.artist,
    ).first()
    if not artist:
        raise HTTPException(404, "Artist not found")

    co = models.CustomOrder(buyer_id=current_user.id, **payload.model_dump())
    db.add(co)
    db.flush()

    db.add(models.Notification(
        user_id = artist.id,
        title   = "New Custom Order Request",
        message = f"You have a new commission request: '{co.title}'.",
    ))
    db.commit()
    db.refresh(co)
    return co


# ── Upload reference images ────────────────────────────────────────────────

@router.post("/{co_id}/images", response_model=schemas.CustomOrderOut)
def upload_reference_images(
    co_id:        int,
    files:        List[UploadFile] = File(...),
    current_user: models.User       = Depends(get_current_user),
    db:           Session           = Depends(get_db),
):
    co = _buyer_owned(co_id, current_user, db)
    urls = list(co.reference_images or [])
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise HTTPException(400, "Unsupported file type")
        fname = f"{co_id}_{uuid.uuid4().hex}{ext}"
        with (UPLOAD_DIR / fname).open("wb") as out:
            shutil.copyfileobj(f.file, out)
        urls.append(f"/static/reference/{fname}")
    co.reference_images = urls
    db.commit()
    db.refresh(co)
    return co


# ── List buyer's custom orders ─────────────────────────────────────────────

@router.get("/my", response_model=List[schemas.CustomOrderOut])
def my_custom_orders(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.CustomOrder)
        .filter(models.CustomOrder.buyer_id == current_user.id)
        .order_by(models.CustomOrder.created_at.desc())
        .all()
    )


# ── Artist: incoming commissions ──────────────────────────────────────────

@router.get("/incoming", response_model=List[schemas.CustomOrderOut])
def incoming_commissions(
    current_user: models.User = Depends(get_current_artist),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.CustomOrder)
        .filter(models.CustomOrder.artist_id == current_user.id)
        .order_by(models.CustomOrder.created_at.desc())
        .all()
    )


# ── Single custom order ────────────────────────────────────────────────────

@router.get("/{co_id}", response_model=schemas.CustomOrderOut)
def get_custom_order(
    co_id:        int,
    current_user: models.User = Depends(get_current_user),
    db:           Session     = Depends(get_db),
):
    co = db.query(models.CustomOrder).filter(models.CustomOrder.id == co_id).first()
    if not co:
        raise HTTPException(404, "Not found")
    if co.buyer_id != current_user.id and co.artist_id != current_user.id:
        raise HTTPException(403, "Access denied")
    return co


# ── Artist: respond to commission ─────────────────────────────────────────

@router.put("/{co_id}", response_model=schemas.CustomOrderOut)
def update_custom_order(
    co_id:        int,
    payload:      schemas.CustomOrderUpdate,
    current_user: models.User = Depends(get_current_artist),
    db:           Session     = Depends(get_db),
):
    co = db.query(models.CustomOrder).filter(
        models.CustomOrder.id == co_id,
        models.CustomOrder.artist_id == current_user.id,
    ).first()
    if not co:
        raise HTTPException(404, "Not found or not your commission")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(co, k, v)

    db.add(models.Notification(
        user_id = co.buyer_id,
        title   = "Commission Update",
        message = f"Your commission '{co.title}' has been updated to '{co.status.value}'.",
    ))
    db.commit()
    db.refresh(co)
    return co


# ── Helper ─────────────────────────────────────────────────────────────────

def _buyer_owned(co_id: int, user: models.User, db: Session) -> models.CustomOrder:
    co = db.query(models.CustomOrder).filter(
        models.CustomOrder.id == co_id,
        models.CustomOrder.buyer_id == user.id,
    ).first()
    if not co:
        raise HTTPException(404, "Custom order not found")
    return co
