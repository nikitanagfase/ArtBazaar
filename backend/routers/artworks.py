"""
routers/artworks.py  –  Artwork listing, creation, update, and image upload.
"""

import os, uuid, shutil, tempfile
from pathlib import Path
from typing import List, Optional

import cloudinary
import cloudinary.uploader

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from database import get_db
import models, schemas
from auth import get_current_user, get_current_artist

router = APIRouter(prefix="/api/artworks", tags=["artworks"])

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGES  = 6


# ── List / Search ──────────────────────────────────────────────────────────

@router.get("", response_model=List[schemas.ArtworkListOut])
def list_artworks(
    q:         Optional[str]                       = Query(None),
    category:  Optional[models.ArtworkCategory]    = Query(None),
    min_price: Optional[float]                     = Query(None, ge=0),
    max_price: Optional[float]                     = Query(None, ge=0),
    artist_id: Optional[int]                       = Query(None),
    sort_by:   str                                 = Query("created_at"),  # created_at | price | views
    order:     str                                 = Query("desc"),
    page:      int                                 = Query(1, ge=1),
    limit:     int                                 = Query(12, ge=1, le=100),
    db:        Session                             = Depends(get_db),
):
    qs = db.query(models.Artwork).filter(models.Artwork.is_available == True)

    if q:
        like = f"%{q}%"
        qs = qs.filter(
            or_(
                models.Artwork.title.ilike(like),
                models.Artwork.description.ilike(like),
            )
        )
    if category:
        qs = qs.filter(models.Artwork.category == category)
    if min_price is not None:
        qs = qs.filter(models.Artwork.price >= min_price)
    if max_price is not None:
        qs = qs.filter(models.Artwork.price <= max_price)
    if artist_id:
        qs = qs.filter(models.Artwork.artist_id == artist_id)

    sort_col = {
        "price":      models.Artwork.price,
        "views":      models.Artwork.view_count,
        "created_at": models.Artwork.created_at,
    }.get(sort_by, models.Artwork.created_at)

    qs = qs.order_by(sort_col.desc() if order == "desc" else sort_col.asc())
    return qs.offset((page - 1) * limit).limit(limit).all()


# ── Featured Artworks ──────────────────────────────────────────────────────

@router.get("/featured", response_model=List[schemas.ArtworkListOut])
def featured_artworks(limit: int = Query(8, le=20), db: Session = Depends(get_db)):
    return (
        db.query(models.Artwork)
        .filter(models.Artwork.is_featured == True, models.Artwork.is_available == True)
        .order_by(models.Artwork.created_at.desc())
        .limit(limit)
        .all()
    )


# ── Single Artwork ─────────────────────────────────────────────────────────

@router.get("/{artwork_id}", response_model=schemas.ArtworkOut)
def get_artwork(artwork_id: int, db: Session = Depends(get_db)):
    art = db.query(models.Artwork).filter(models.Artwork.id == artwork_id).first()
    if not art:
        raise HTTPException(404, "Artwork not found")
    art.view_count += 1
    db.commit()
    db.refresh(art)
    return art


# ── Create Artwork (artist only) ──────────────────────────────────────────

@router.post("", response_model=schemas.ArtworkOut, status_code=201)
def create_artwork(
    payload: schemas.ArtworkCreate,
    current_user: models.User = Depends(get_current_artist),
    db: Session = Depends(get_db),
):
    art = models.Artwork(artist_id=current_user.id, **payload.model_dump())
    db.add(art)
    db.commit()
    db.refresh(art)
    return art


# ── Update Artwork ─────────────────────────────────────────────────────────

@router.put("/{artwork_id}", response_model=schemas.ArtworkOut)
def update_artwork(
    artwork_id: int,
    payload: schemas.ArtworkUpdate,
    current_user: models.User = Depends(get_current_artist),
    db: Session = Depends(get_db),
):
    art = _owned_artwork(artwork_id, current_user, db)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(art, k, v)
    db.commit()
    db.refresh(art)
    return art


# ── Delete Artwork ─────────────────────────────────────────────────────────

@router.delete("/{artwork_id}", status_code=204)
def delete_artwork(
    artwork_id: int,
    current_user: models.User = Depends(get_current_artist),
    db: Session = Depends(get_db),
):
    art = _owned_artwork(artwork_id, current_user, db)
    db.delete(art)
    db.commit()


# ── Upload Images ──────────────────────────────────────────────────────────

@router.post("/{artwork_id}/images", response_model=schemas.ArtworkOut)
def upload_artwork_images(
    artwork_id: int,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    current_user: models.User = Depends(get_current_artist),
    db: Session = Depends(get_db),
):
    art = _owned_artwork(artwork_id, current_user, db)

    if len(art.image_urls or []) + len(files) > MAX_IMAGES:
        raise HTTPException(400, f"Maximum {MAX_IMAGES} images per artwork")

    saved_urls = list(art.image_urls or [])
    first_image_path = None

    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(400, f"Unsupported file type: {ext}")

        # Save to a temp file first (needed for CLIP embedding computation)
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            shutil.copyfileobj(f.file, tmp)
            tmp_path = tmp.name

        # Upload to Cloudinary (persistent storage, survives redeploys)
        result = cloudinary.uploader.upload(
            tmp_path,
            folder="artbazaar/artworks",
            public_id=f"{artwork_id}_{uuid.uuid4().hex}",
        )
        saved_urls.append(result["secure_url"])

        if first_image_path is None:
            first_image_path = tmp_path
        else:
            os.remove(tmp_path)  # cleanup temp files we don't need anymore

    art.image_urls = saved_urls
    db.commit()
    db.refresh(art)

    # ── Compute CLIP embedding in background ──
    if first_image_path:
        from routers.ai import compute_and_store_embedding
        background_tasks.add_task(
            compute_and_store_embedding,
            artwork_id,
            first_image_path,
            db,
        )

    return art


# ── Delete single image ────────────────────────────────────────────────────

@router.delete("/{artwork_id}/images/{img_index}", response_model=schemas.ArtworkOut)
def delete_artwork_image(
    artwork_id: int,
    img_index:  int,
    current_user: models.User = Depends(get_current_artist),
    db: Session = Depends(get_db),
):
    art = _owned_artwork(artwork_id, current_user, db)
    urls = list(art.image_urls or [])
    if img_index < 0 or img_index >= len(urls):
        raise HTTPException(400, "Invalid image index")

    urls.pop(img_index)
    art.image_urls = urls
    db.commit()
    db.refresh(art)
    return art


# ── Reviews ────────────────────────────────────────────────────────────────

@router.get("/{artwork_id}/reviews", response_model=List[schemas.ReviewOut])
def get_reviews(artwork_id: int, db: Session = Depends(get_db)):
    _assert_artwork_exists(artwork_id, db)
    return (
        db.query(models.Review)
        .filter(models.Review.artwork_id == artwork_id)
        .order_by(models.Review.created_at.desc())
        .all()
    )


@router.post("/{artwork_id}/reviews", response_model=schemas.ReviewOut, status_code=201)
def add_review(
    artwork_id: int,
    payload: schemas.ReviewCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _assert_artwork_exists(artwork_id, db)
    existing = (
        db.query(models.Review)
        .filter(
            models.Review.artwork_id == artwork_id,
            models.Review.reviewer_id == current_user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(409, "You have already reviewed this artwork")

    review = models.Review(
        artwork_id  = artwork_id,
        reviewer_id = current_user.id,
        **payload.model_dump(),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


# ── Wishlist ────────────────────────────────────────────────────────────────

@router.post("/{artwork_id}/wishlist", status_code=201)
def add_to_wishlist(
    artwork_id:   int,
    current_user: models.User = Depends(get_current_user),
    db:           Session     = Depends(get_db),
):
    _assert_artwork_exists(artwork_id, db)
    if db.query(models.Wishlist).filter_by(
        user_id=current_user.id, artwork_id=artwork_id
    ).first():
        raise HTTPException(409, "Already in wishlist")

    db.add(models.Wishlist(user_id=current_user.id, artwork_id=artwork_id))
    db.commit()
    return {"detail": "added to wishlist"}


@router.delete("/{artwork_id}/wishlist", status_code=204)
def remove_from_wishlist(
    artwork_id:   int,
    current_user: models.User = Depends(get_current_user),
    db:           Session     = Depends(get_db),
):
    entry = db.query(models.Wishlist).filter_by(
        user_id=current_user.id, artwork_id=artwork_id
    ).first()
    if not entry:
        raise HTTPException(404, "Not in wishlist")
    db.delete(entry)
    db.commit()


# ── Helpers ────────────────────────────────────────────────────────────────

def _owned_artwork(
    artwork_id: int,
    current_user: models.User,
    db: Session,
) -> models.Artwork:
    art = db.query(models.Artwork).filter(models.Artwork.id == artwork_id).first()
    if not art:
        raise HTTPException(404, "Artwork not found")
    if art.artist_id != current_user.id:
        raise HTTPException(403, "Not your artwork")
    return art


def _assert_artwork_exists(artwork_id: int, db: Session):
    if not db.query(models.Artwork).filter(models.Artwork.id == artwork_id).first():
        raise HTTPException(404, "Artwork not found")