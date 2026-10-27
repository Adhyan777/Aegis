from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.services.fraud_detection import analyze_transaction
from app.services.ml_anomaly_detection import analyze_ml_anomaly


def analyze_fraud_intelligence(
    transaction: Transaction,
    db: Session,
    history: list[Transaction] | None = None,
) -> dict:
    """Combine rule-based fraud detection with statistical anomaly signals."""

    # 1. Run the existing rule-based fraud analysis.
    rule_result = analyze_transaction(transaction)
    rule_score = float(rule_result.get("risk_score") or 0)

    # 2. Run statistical anomaly detection using the supplied transaction history.
    anomaly_result = analyze_ml_anomaly(
        transaction,
        db,
        history=history,
    )

    anomaly_score_value = anomaly_result.get("anomaly_score")
    anomaly_available = (
        anomaly_result.get("ml_available", False)
        and anomaly_score_value is not None
    )

    anomaly_score = (
        float(anomaly_score_value)
        if anomaly_available
        else None
    )

    # 3. Combine scores when sufficient history is available.
    if anomaly_score is not None:
        weighted_score = rule_score * 0.65 + anomaly_score * 0.35
        combined_score = max(
            rule_score,
            weighted_score,
            anomaly_score * 0.80,
        )
    else:
        combined_score = rule_score

    combined_score = round(min(100.0, combined_score), 2)

    # 4. Assign the overall risk level.
    if combined_score >= 50:
        risk_level = "high"
    elif combined_score >= 25:
        risk_level = "medium"
    else:
        risk_level = "low"

    # 5. Collect explanations from both detection methods.
    explanations = []

    for reason in rule_result.get("reasons", []):
        explanations.append({
            "source": "rule_based",
            "reason": reason,
        })

    for reason in anomaly_result.get("reasons", []):
        explanations.append({
            "source": "statistical_anomaly",
            "reason": reason,
        })

    # 6. Return the combined fraud intelligence result.
    return {
        "transaction_id": str(transaction.id),
        "transaction_reference": transaction.transaction_reference,
        "customer_id": transaction.customer_id,
        "amount": float(transaction.amount),
        "currency": transaction.currency,
        "rule_based_score": round(rule_score, 2),
        "anomaly_score": anomaly_score,
        "anomaly_available": anomaly_available,
        "combined_risk_score": combined_score,
        "risk_level": risk_level,
        "is_suspicious": combined_score >= 50,
        "rule_analysis": rule_result,
        "anomaly_analysis": anomaly_result,
        "explanations": explanations,
        "scoring_method": (
            "65% rule-based and 35% statistical anomaly score, "
            "with safeguards to preserve strong individual signals. "
            "When anomaly history is insufficient, the rule-based "
            "score is used alone."
        ),
        "score_is_probability": False,
    }
