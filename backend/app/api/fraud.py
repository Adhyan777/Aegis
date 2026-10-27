
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.transaction import Transaction
from app.services.fraud_detection import (
    analyze_transaction,
    analyze_all_transactions,
    get_fraud_summary,
)
from app.services.ml_anomaly_detection import analyze_ml_anomaly
from app.services.fraud_intelligence import analyze_fraud_intelligence

router = APIRouter(
    prefix="/api/fraud",
    tags=["Fraud Detection"],
)


@router.get("/analyze/{transaction_id}")
def analyze_existing_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
):
    transaction = db.get(Transaction, transaction_id)

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found.",
        )

    result = analyze_transaction(transaction)
    result["ml_analysis"] = analyze_ml_anomaly(transaction, db)

    return result


@router.get("/analyze-all")
def analyze_all_existing_transactions(
    db: Session = Depends(get_db),
):
    results = analyze_all_transactions(db)

    transactions = db.scalars(
        select(Transaction)
    ).all()

    transaction_by_id = {
        str(item.id): item
        for item in transactions
    }

    history = list(transactions)

    for result in results:
        transaction = transaction_by_id.get(
            result["transaction_id"]
        )

        if transaction is not None:
            result["ml_analysis"] = analyze_ml_anomaly(
                transaction,
                db,
                history=history,
            )

    return results


@router.get("/ml/analyze/{transaction_id}")
def analyze_transaction_with_ml(
    transaction_id: UUID,
    db: Session = Depends(get_db),
):
    transaction = db.get(Transaction, transaction_id)

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found.",
        )

    return analyze_ml_anomaly(transaction, db)


@router.get("/intelligence/{transaction_id}")
def get_fraud_intelligence(
    transaction_id: UUID,
    db: Session = Depends(get_db),
):
    transaction = db.get(Transaction, transaction_id)

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found.",
        )

    history = db.scalars(select(Transaction)).all()

    return analyze_fraud_intelligence(
        transaction,
        db,
        history=history,
    )


@router.get("/intelligence-all")
def get_all_fraud_intelligence(
    db: Session = Depends(get_db),
):
    history = db.scalars(
        select(Transaction).order_by(
            Transaction.transaction_time.desc()
        )
    ).all()

    return [
        analyze_fraud_intelligence(
            transaction,
            db,
            history=history,
        )
        for transaction in history
    ]


@router.get("/summary")
def fraud_risk_summary(
    db: Session = Depends(get_db),
):
    return get_fraud_summary(db)
