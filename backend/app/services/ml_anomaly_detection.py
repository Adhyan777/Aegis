
from datetime import datetime, timedelta
from statistics import median


MIN_TRAINING_TRANSACTIONS = 10
ANOMALY_THRESHOLD = 40


def _normalise_datetime(value):
    """Make timestamps comparable without changing stored database values."""
    if value is None:
        return None

    if value.tzinfo is not None:
        return value.replace(tzinfo=None)

    return value


def _amount(transaction):
    try:
        return float(transaction.amount or 0)
    except (TypeError, ValueError):
        return 0.0


def analyze_ml_anomaly(transaction, db, history=None):
    """
    Explainable statistical anomaly scoring.

    This is a heuristic detector, not a trained machine-learning model.
    Scores are risk indicators, not probabilities of fraud.
    """
    if history is None:
        history = (
            db.query(type(transaction))
            .order_by(type(transaction).transaction_time.asc())
            .all()
        )

    transaction_time = _normalise_datetime(
        transaction.transaction_time
    )
    transaction_amount = _amount(transaction)
    customer_id = transaction.customer_id

    # Only use earlier transactions as historical evidence.
    prior_transactions = []

    for item in history:
        if item.id == transaction.id:
            continue

        item_time = _normalise_datetime(item.transaction_time)

        if (
            transaction_time is not None
            and item_time is not None
            and item_time < transaction_time
        ):
            prior_transactions.append(item)

    if len(prior_transactions) < MIN_TRAINING_TRANSACTIONS:
        return {
            "ml_available": False,
            "anomaly_score": None,
            "is_anomaly": False,
            "risk_level": "unavailable",
            "reason": "Insufficient prior transaction history.",
            "reasons": [],
            "features": {},
            "model_name": "StatisticalAnomalyHeuristic",
            "note": (
                "This is a statistical heuristic, not a trained ML model "
                "or a probability of fraud."
            ),
        }

    score = 0
    reasons = []

    # Feature 1: unusually large transaction relative to global history.
    historical_amounts = [
        _amount(item)
        for item in prior_transactions
        if _amount(item) > 0
    ]

    global_median = (
        median(historical_amounts)
        if historical_amounts
        else 0
    )

    if global_median > 0 and transaction_amount >= global_median * 5:
        score += 25
        reasons.append(
            "Transaction amount is at least 5x the historical median."
        )
    elif global_median > 0 and transaction_amount >= global_median * 3:
        score += 15
        reasons.append(
            "Transaction amount is at least 3x the historical median."
        )

    # Feature 2: unusual spending relative to this customer's own history.
    customer_history = [
        item
        for item in prior_transactions
        if item.customer_id == customer_id
    ]

    customer_amounts = [
        _amount(item)
        for item in customer_history
        if _amount(item) > 0
    ]

    customer_median = (
        median(customer_amounts)
        if customer_amounts
        else 0
    )

    if customer_median > 0:
        if transaction_amount >= customer_median * 10:
            score += 45
            reasons.append(
                "Amount is at least 10x this customer's typical transaction."
            )
        elif transaction_amount >= customer_median * 5:
            score += 35
            reasons.append(
                "Amount is at least 5x this customer's typical transaction."
            )
        elif transaction_amount >= customer_median * 3:
            score += 20
            reasons.append(
                "Amount is at least 3x this customer's typical transaction."
            )

    # Feature 3: repeated transactions by the same customer in the prior hour.
    recent_cutoff = (
        transaction_time - timedelta(hours=1)
        if transaction_time is not None
        else None
    )

    recent_customer_transactions = []

    if transaction_time is not None:
        for item in customer_history:
            item_time = _normalise_datetime(item.transaction_time)

            if (
                item_time is not None
                and recent_cutoff <= item_time < transaction_time
            ):
                recent_customer_transactions.append(item)

    recent_count = len(recent_customer_transactions)

    if recent_count >= 5:
        score += 45
        reasons.append(
            f"{recent_count} earlier transactions by this customer "
            "occurred within one hour."
        )
    elif recent_count >= 3:
        score += 40
        reasons.append(
            f"{recent_count} earlier transactions by this customer "
            "occurred within one hour."
        )
    elif recent_count >= 2:
        score += 25
        reasons.append(
            f"{recent_count} earlier transactions by this customer "
            "occurred within one hour."
        )

    # Feature 4: declined/failed status is a risk signal, not proof of fraud.
    status = str(transaction.status or "").strip().lower()

    if status in {"declined", "failed", "failure"}:
        score += 40
        reasons.append(
            f"Transaction status is '{status}'."
        )

    # Feature 5: overnight activity adds a smaller contextual signal.
    if transaction_time is not None and transaction_time.hour < 5:
        score += 10
        reasons.append(
            "Transaction occurred during overnight hours (00:00–04:59)."
        )

    # Feature 6: missing location is weak evidence only.
    if not transaction.location:
        score += 5
        reasons.append("Transaction location is missing.")

    score = min(100, score)

    if score >= 70:
        risk_level = "high"
    elif score >= ANOMALY_THRESHOLD:
        risk_level = "medium"
    else:
        risk_level = "low"

    is_anomaly = score >= ANOMALY_THRESHOLD

    return {
        "ml_available": True,
        "anomaly_score": round(float(score), 2),
        "is_anomaly": is_anomaly,
        "risk_level": risk_level,
        "reason": (
            "; ".join(reasons)
            if reasons
            else "No strong anomaly signals were identified."
        ),
        "reasons": reasons,
        "features": {
            "transaction_amount": transaction_amount,
            "global_median_amount": round(global_median, 2),
            "customer_median_amount": round(customer_median, 2),
            "recent_customer_transaction_count": recent_count,
            "transaction_status": status,
            "transaction_hour": (
                transaction_time.hour
                if transaction_time is not None
                else None
            ),
            "prior_transaction_count": len(prior_transactions),
        },
        "model_name": "StatisticalAnomalyHeuristic",
        "note": (
            "This is an explainable statistical heuristic, not a trained "
            "ML model. The score is not a probability of fraud."
        ),
    }
