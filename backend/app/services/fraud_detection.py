
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


# Initial rule-based threshold.
HIGH_AMOUNT_THRESHOLD = Decimal("10000.00")


def analyze_transaction(transaction: Transaction) -> dict:
    """Analyze one transaction using basic fraud detection rules."""

    risk_score = 0
    reasons = []

    amount = Decimal(str(transaction.amount))

    if amount >= HIGH_AMOUNT_THRESHOLD:
        risk_score += 50
        reasons.append(
            "Transaction amount meets or exceeds the high-value threshold."
        )
    if (
        transaction.transaction_type.lower() == "refund"
        and amount >= Decimal("5000.00")
    ):
        risk_score += 25
        reasons.append(
            "Refund amount meets or exceeds the large-refund threshold."
        )
    if transaction.status.lower() in {"failed", "declined"}:
        risk_score += 25
        reasons.append(
            "Transaction has a failed or declined status."
        )
    if risk_score >= 50:
        risk_level = "high"
    elif risk_score >= 25:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "transaction_id": str(transaction.id),
        "transaction_reference": transaction.transaction_reference,
        "customer_id": transaction.customer_id,
        "amount": str(amount),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "is_suspicious": risk_score >= 50,
        "reasons": reasons,
    }


def analyze_all_transactions(db: Session) -> list[dict]:
    """Analyze every transaction in the database."""

    transactions = db.scalars(
        select(Transaction).order_by(Transaction.transaction_time.desc())
    ).all()

    return [
        analyze_transaction(transaction)
        for transaction in transactions
    ]


def get_fraud_summary(db: Session) -> dict:
    """Summarize fraud risk across all stored transactions."""

    analyses = analyze_all_transactions(db)

    risk_breakdown = {
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for analysis in analyses:
        risk_level = analysis["risk_level"]
        if risk_level in risk_breakdown:
            risk_breakdown[risk_level] += 1

    review_queue = [
        analysis
        for analysis in analyses
        if analysis["risk_level"] in {"medium", "high"}
    ]

    return {
        "total_analyzed": len(analyses),
        "suspicious_transactions": sum(
            1 for analysis in analyses
            if analysis["is_suspicious"]
        ),
        "risk_breakdown": risk_breakdown,
        "transactions_for_review": review_queue,
    }
