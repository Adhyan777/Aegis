
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


def get_transaction_summary(db: Session) -> dict:
    """Return summary statistics for all transactions."""

    total_transactions = db.scalar(
        select(func.count(Transaction.id))
    ) or 0

    total_amount = db.scalar(
        select(func.sum(Transaction.amount))
    ) or Decimal("0.00")

    status_query = select(
        Transaction.status,
        func.count(Transaction.id).label("count"),
    ).group_by(Transaction.status)

    status_rows = db.execute(status_query).all()

    status_breakdown = {
        status: count for status, count in status_rows
    }

    payment_query = select(
        Transaction.payment_method,
        func.count(Transaction.id).label("count"),
    ).group_by(Transaction.payment_method)

    payment_rows = db.execute(payment_query).all()

    payment_method_breakdown = {
        method: count for method, count in payment_rows
    }

    type_query = select(
        Transaction.transaction_type,
        func.count(Transaction.id).label("count"),
    ).group_by(Transaction.transaction_type)

    type_rows = db.execute(type_query).all()

    transaction_type_breakdown = {
        transaction_type: count
        for transaction_type, count in type_rows
    }

    return {
        "total_transactions": total_transactions,
        "total_amount": str(total_amount),
        "status_breakdown": status_breakdown,
        "payment_method_breakdown": payment_method_breakdown,
        "transaction_type_breakdown": transaction_type_breakdown,
    }


def get_daily_transaction_trends(db: Session) -> list[dict]:
    """Return daily transaction counts and amounts."""

    transactions = db.execute(
        select(
            Transaction.transaction_time,
            Transaction.amount,
        ).order_by(Transaction.transaction_time)
    ).all()

    daily_data = {}

    for transaction_time, amount in transactions:
        day = transaction_time.date().isoformat()

        if day not in daily_data:
            daily_data[day] = {
                "date": day,
                "transaction_count": 0,
                "total_amount": Decimal("0.00"),
            }

        daily_data[day]["transaction_count"] += 1
        daily_data[day]["total_amount"] += amount

    return [
        {
            "date": item["date"],
            "transaction_count": item["transaction_count"],
            "total_amount": str(item["total_amount"]),
        }
        for item in daily_data.values()
    ]


def get_customer_transaction_analytics(db: Session) -> list[dict]:
    """Return transaction statistics grouped by customer."""

    query = (
        select(
            Transaction.customer_id,
            func.count(Transaction.id).label("transaction_count"),
            func.sum(Transaction.amount).label("total_amount"),
            func.avg(Transaction.amount).label("average_amount"),
        )
        .group_by(Transaction.customer_id)
        .order_by(func.sum(Transaction.amount).desc())
    )

    rows = db.execute(query).all()

    return [
        {
            "customer_id": row.customer_id,
            "transaction_count": row.transaction_count,
            "total_amount": str(row.total_amount or Decimal("0.00")),
            "average_amount": str(
                row.average_amount or Decimal("0.00")
            ),
        }
        for row in rows
    ]


def get_payment_method_analytics(db: Session) -> list[dict]:
    """Return transaction statistics grouped by payment method."""

    query = (
        select(
            Transaction.payment_method,
            func.count(Transaction.id).label("transaction_count"),
            func.sum(Transaction.amount).label("total_amount"),
            func.avg(Transaction.amount).label("average_amount"),
        )
        .group_by(Transaction.payment_method)
        .order_by(func.sum(Transaction.amount).desc())
    )

    rows = db.execute(query).all()

    return [
        {
            "payment_method": row.payment_method,
            "transaction_count": row.transaction_count,
            "total_amount": str(row.total_amount or Decimal("0.00")),
            "average_amount": str(
                row.average_amount or Decimal("0.00")
            ),
        }
        for row in rows
    ]
