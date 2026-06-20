"""
routers/orders.py  –  Order placement and status management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models, schemas
from auth import get_current_user, get_current_artist

router = APIRouter(prefix="/api/orders", tags=["orders"])


# ── Buyer: place order ─────────────────────────────────────────────────────

@router.post("", response_model=schemas.OrderOut, status_code=201)
def place_order(
    payload: schemas.OrderCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = 0.0
    items_data = []

    for item in payload.items:
        art = db.query(models.Artwork).filter(
            models.Artwork.id == item.artwork_id,
            models.Artwork.is_available == True,
        ).first()
        if not art:
            raise HTTPException(404, f"Artwork {item.artwork_id} not found or unavailable")
        if art.stock < item.quantity:
            raise HTTPException(400, f"Insufficient stock for artwork '{art.title}'")

        line_total = art.price * item.quantity
        total += line_total
        items_data.append((art, item.quantity))

    order = models.Order(
        buyer_id         = current_user.id,
        total_amount     = round(total, 2),
        shipping_address = payload.shipping_address,
        notes            = payload.notes,
    )
    db.add(order)
    db.flush()   # get order.id without commit

    for art, qty in items_data:
        db.add(models.OrderItem(
            order_id   = order.id,
            artwork_id = art.id,
            quantity   = qty,
            unit_price = art.price,
        ))
        art.stock -= qty
        if art.stock == 0:
            art.is_available = False

    # Notify artists
    artist_ids = {art.artist_id for art, _ in items_data}
    for aid in artist_ids:
        db.add(models.Notification(
            user_id = aid,
            title   = "New Order Received",
            message = f"You have a new order #{order.id}.",
        ))

    db.commit()
    db.refresh(order)
    return order


# ── Buyer: my orders ───────────────────────────────────────────────────────

@router.get("/my", response_model=List[schemas.OrderOut])
def my_orders(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Order)
        .filter(models.Order.buyer_id == current_user.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )


@router.get("/my/wishlist", response_model=List[schemas.WishlistOut])
def my_wishlist(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Wishlist)
        .filter(models.Wishlist.user_id == current_user.id)
        .all()
    )


# ── Artist: incoming orders ────────────────────────────────────────────────

@router.get("/incoming", response_model=List[schemas.OrderOut])
def incoming_orders(
    current_user: models.User = Depends(get_current_artist),
    db: Session = Depends(get_db),
):
    """Returns orders that contain at least one artwork by this artist."""
    orders = (
        db.query(models.Order)
        .join(models.OrderItem)
        .join(models.Artwork)
        .filter(models.Artwork.artist_id == current_user.id)
        .distinct()
        .order_by(models.Order.created_at.desc())
        .all()
    )
    return orders


# ── Single order ───────────────────────────────────────────────────────────

@router.get("/{order_id}", response_model=schemas.OrderOut)
def get_order(
    order_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    # Buyers can view their own; artists can view orders containing their work
    if order.buyer_id == current_user.id:
        return order

    has_item = any(
        item.artwork.artist_id == current_user.id for item in order.items
    )
    if has_item:
        return order

    raise HTTPException(403, "Access denied")


# ── Update order status (artist) ──────────────────────────────────────────

@router.put("/{order_id}/status", response_model=schemas.OrderOut)
def update_status(
    order_id: int,
    payload: schemas.OrderStatusUpdate,
    current_user: models.User = Depends(get_current_artist),
    db: Session = Depends(get_db),
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    has_item = any(
        item.artwork.artist_id == current_user.id for item in order.items
    )
    if not has_item:
        raise HTTPException(403, "Not your order")

    order.status = payload.status

    db.add(models.Notification(
        user_id = order.buyer_id,
        title   = "Order Status Updated",
        message = f"Your order #{order.id} is now '{payload.status.value}'.",
    ))
    db.commit()
    db.refresh(order)
    return order
