"""
routers/ai.py  –  AI-powered features using Google Gemini
"""

import os, io, base64, json
from typing import List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import numpy as np
import PIL.Image

from database import get_db
import models, schemas
from auth import get_current_user

router = APIRouter(prefix="/api/ai", tags=["AI"])


# ── Gemini setup ───────────────────────────────────────────────────────────
def _get_gemini_client():
    from google import genai
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise HTTPException(503, "Gemini API key not configured")
    return genai.Client(api_key=key)


# ── CLIP setup ─────────────────────────────────────────────────────────────
def _get_clip():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("clip-ViT-B-32")
    except Exception as exc:
        raise HTTPException(503, f"CLIP model unavailable: {exc}")


# ── 1. Recommendations ─────────────────────────────────────────────────────
@router.get("/recommendations", response_model=List[schemas.ArtworkListOut])
def get_recommendations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 8,
):
    ordered_ids: set[int] = set()
    categories: List[str] = []

    orders = db.query(models.Order).filter(models.Order.buyer_id == current_user.id).all()
    for order in orders:
        for item in order.items:
            ordered_ids.add(item.artwork_id)
            categories.append(item.artwork.category.value)

    wl = db.query(models.Wishlist).filter(models.Wishlist.user_id == current_user.id).all()
    wishlisted_ids: set[int] = {w.artwork_id for w in wl}
    for w in wl:
        categories.append(w.artwork.category.value)

    exclude_ids = ordered_ids | wishlisted_ids
    base_qs = db.query(models.Artwork).filter(models.Artwork.is_available == True)
    if exclude_ids:
        base_qs = base_qs.filter(~models.Artwork.id.in_(exclude_ids))

    if categories:
        from collections import Counter
        top_cat = Counter(categories).most_common(2)
        cat_values = [c for c, _ in top_cat]
        results = (
            base_qs
            .filter(models.Artwork.category.in_(cat_values))
            .order_by(models.Artwork.view_count.desc())
            .limit(limit)
            .all()
        )
        if len(results) >= limit:
            return results
        extra = (
            base_qs
            .filter(~models.Artwork.id.in_({r.id for r in results}))
            .order_by(models.Artwork.view_count.desc())
            .limit(limit - len(results))
            .all()
        )
        return results + extra

    return base_qs.order_by(models.Artwork.view_count.desc()).limit(limit).all()


# ── 2. AI Description Generator (Gemini) ──────────────────────────────────
@router.post("/generate-description", response_model=schemas.AIDescriptionOut)
async def generate_description(
    file: UploadFile = File(...),
    _: models.User = Depends(get_current_user),
):
    from google import genai
    from google.genai import types

    client = _get_gemini_client()

    img_bytes = await file.read()
    pil_img = PIL.Image.open(io.BytesIO(img_bytes)).convert("RGB")

    prompt = (
        "You are an expert art curator. Analyse this artwork image and respond ONLY "
        "with valid JSON (no markdown, no extra text) in this exact format:\n"
        '{"title":"...","description":"...","tags":["tag1","tag2","tag3","tag4","tag5"]}\n'
        "The description should be 2-3 engaging sentences. "
        "Tags should be lowercase single-word or short-phrase descriptors."
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, pil_img],
        )
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            raise HTTPException(
                status_code=429,
                detail="AI quota limit reached. Please try again later."
            )
        raise HTTPException(status_code=500, detail=f"AI service error: {err_str}")

    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(500, "AI returned malformed JSON")

    return schemas.AIDescriptionOut(**data)

# ── 3. Image Similarity Search ─────────────────────────────────────────────
@router.post("/similar", response_model=List[schemas.SimilarArtworkOut])
async def find_similar(
    file: UploadFile = File(...),
    limit: int = 6,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    img_bytes = await file.read()
    pil_img = PIL.Image.open(io.BytesIO(img_bytes)).convert("RGB")

    model = _get_clip()
    query_emb = np.array(model.encode(pil_img), dtype=np.float32)

    artworks = (
        db.query(models.Artwork)
        .filter(
            models.Artwork.is_available == True,
            models.Artwork.embedding.isnot(None),
        )
        .all()
    )
    if not artworks:
        return []

    scored = []
    for art in artworks:
        stored = np.array(art.embedding, dtype=np.float32)
        cos_sim = float(
            np.dot(query_emb, stored)
            / (np.linalg.norm(query_emb) * np.linalg.norm(stored) + 1e-9)
        )
        scored.append((art, cos_sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [
        schemas.SimilarArtworkOut(artwork=art, score=round(score, 4))
        for art, score in scored[:limit]
    ]


# ── Background: compute CLIP embedding ────────────────────────────────────
def compute_and_store_embedding(artwork_id: int, image_path: str, db: Session):
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("clip-ViT-B-32")
        img = PIL.Image.open(image_path).convert("RGB")
        emb = model.encode(img).tolist()

        art = db.query(models.Artwork).filter(models.Artwork.id == artwork_id).first()
        if art:
            art.embedding = emb
            db.commit()
    except Exception as exc:
        print(f"[AI] Embedding failed for artwork {artwork_id}: {exc}")