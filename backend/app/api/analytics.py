
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.analytics import (
    get_transaction_summary,
    get_daily_transaction_trends,
    get_customer_transaction_analytics,
    get_payment_method_analytics,
)

router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"],
)


@router.get("/summary")
def transaction_summary(
    db: Session = Depends(get_db),
):
    return get_transaction_summary(db)


@router.get("/daily-trends")
def daily_transaction_trends(
    db: Session = Depends(get_db),
):
    return get_daily_transaction_trends(db)


@router.get("/customers")
def customer_transaction_analytics(
    db: Session = Depends(get_db),
):
    return get_customer_transaction_analytics(db)


@router.get("/payment-methods")
def payment_method_analytics(
    db: Session = Depends(get_db),
):
    return get_payment_method_analytics(db)
