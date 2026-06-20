"""
routers/analytics.py  –  Artist performance analytics endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from collections import defaultdict

from database import get_db
import models, schemas
from auth import get_current_artist

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/artist", response_model=schemas.ArtistAnalytics)
def artist_analytics(
    current_user: models.User = Depends(get_current_artist),
    db: Session = Depends(get_db),
):
    artist_id = current_user.id

    # Total artworks
    total_artworks = db.query(func.count(models.Artwork.id)).filter(
        models.Artwork.artist_id == artist_id
    ).scalar() or 0

    # Orders containing this artist's artworks
    order_ids = (
        db.query(models.OrderItem.order_id)
        .join(models.Artwork)
        .filter(models.Artwork.artist_id == artist_id)
        .distinct()
        .all()
    )
    order_id_list = [o[0] for o in order_ids]
    total_orders = len(order_id_list)

    # Revenue = sum of (unit_price * quantity) for this artist's items
    revenue_data = (
        db.query(
            func.sum(models.OrderItem.unit_price * models.OrderItem.quantity)
        )
        .join(models.Artwork)
        .filter(models.Artwork.artist_id == artist_id)
        .scalar()
    )
    total_revenue = float(revenue_data or 0)

    # Pending orders
    pending_orders = (
        db.query(func.count(models.Order.id))
        .filter(
            models.Order.id.in_(order_id_list),
            models.Order.status == models.OrderStatus.pending,
        )
        .scalar()
        or 0
    )

    # Average rating
    avg_rating = (
        db.query(func.avg(models.Review.rating))
        .join(models.Artwork)
        .filter(models.Artwork.artist_id == artist_id)
        .scalar()
    )
    average_rating = round(float(avg_rating or 0), 2)

    # Top category
    cat_row = (
        db.query(models.Artwork.category, func.count(models.Artwork.id).label("cnt"))
        .filter(models.Artwork.artist_id == artist_id)
        .group_by(models.Artwork.category)
        .order_by(func.count(models.Artwork.id).desc())
        .first()
    )
    top_category = cat_row[0].value if cat_row else None

    # Monthly revenue (last 12 months)
    monthly_raw = (
        db.query(
            extract("year",  models.Order.created_at).label("yr"),
            extract("month", models.Order.created_at).label("mo"),
            func.sum(models.OrderItem.unit_price * models.OrderItem.quantity).label("rev"),
        )
        .join(models.OrderItem, models.Order.id == models.OrderItem.order_id)
        .join(models.Artwork,   models.OrderItem.artwork_id == models.Artwork.id)
        .filter(models.Artwork.artist_id == artist_id)
        .group_by("yr", "mo")
        .order_by("yr", "mo")
        .all()
    )
    monthly_revenue = [
        {"month": f"{int(r.yr)}-{int(r.mo):02d}", "revenue": round(float(r.rev), 2)}
        for r in monthly_raw
    ]

    # Recent orders (last 5)
    recent_orders = (
        db.query(models.Order)
        .filter(models.Order.id.in_(order_id_list))
        .order_by(models.Order.created_at.desc())
        .limit(5)
        .all()
    )

    return schemas.ArtistAnalytics(
        total_artworks  = total_artworks,
        total_orders    = total_orders,
        total_revenue   = total_revenue,
        pending_orders  = pending_orders,
        average_rating  = average_rating,
        top_category    = top_category,
        monthly_revenue = monthly_revenue,
        recent_orders   = recent_orders,
    )
