from datetime import datetime, timedelta, timezone
from random import Random
from uuid import uuid4

from sqlalchemy import select

from app.db.database import SessionLocal
from app.models.transaction import Transaction
from app.services.ml_anomaly_detection import analyze_ml_anomaly


SEED = 42
CASES_PER_CLASS = 50
THRESHOLD = 40


def calculate_metrics(actual, predicted):
    tp = sum(a and p for a, p in zip(actual, predicted))
    tn = sum((not a) and (not p) for a, p in zip(actual, predicted))
    fp = sum((not a) and p for a, p in zip(actual, predicted))
    fn = sum(a and (not p) for a, p in zip(actual, predicted))

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    fpr = fp / (fp + tn) if fp + tn else 0.0

    return {
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fpr,
    }


def main():
    rng = Random(SEED)
    db = SessionLocal()

    try:
        history = db.scalars(
            select(Transaction)
        ).all()

        if len(history) < 10:
            print("Need at least 10 existing transactions.")
            return

        latest_time = max(t.transaction_time for t in history)
        base_time = latest_time + timedelta(days=1)

        # Match the timestamp format returned by the database.
        if latest_time.tzinfo is None:
            base_time = base_time.replace(tzinfo=None)
        else:
            base_time = base_time.astimezone(timezone.utc)

        cases = []

        # Normal test cases: moderate amounts, daytime, successful.
        for i in range(CASES_PER_CLASS):
            customer = f"CUST-{rng.randint(1, 100):03d}"

            transaction = Transaction(
                id=uuid4(),
                transaction_reference=f"EVAL-N-{i + 1:03d}",
                customer_id=customer,
                amount=round(rng.uniform(100, 2500), 2),
                currency="INR",
                transaction_type="purchase",
                payment_method="upi",
                status="completed",
                location="Pune",
                transaction_time=(
                    base_time + timedelta(days=i)
                ).replace(hour=12, minute=0, second=0, microsecond=0),
            )

            cases.append((transaction, False))

        # Suspicious test cases: large amounts, overnight, declined.
        for i in range(CASES_PER_CLASS):
            customer = f"CUST-{rng.randint(1, 100):03d}"

            transaction = Transaction(
                id=uuid4(),
                transaction_reference=f"EVAL-S-{i + 1:03d}",
                customer_id=customer,
                amount=round(rng.uniform(25000, 50000), 2),
                currency="INR",
                transaction_type="purchase",
                payment_method="credit_card",
                status="declined",
                location="Mumbai",
                transaction_time=(
                    base_time
                    + timedelta(days=CASES_PER_CLASS + i)
                ).replace(hour=2, minute=0, second=0, microsecond=0),
            )

            cases.append((transaction, True))

        actual = []
        predicted = []

        for transaction, is_suspicious in cases:
            result = analyze_ml_anomaly(
                transaction,
                db,
                history=history,
            )

            score = result.get("anomaly_score")
            predicted_anomaly = (
                score is not None and float(score) >= THRESHOLD
            )

            actual.append(is_suspicious)
            predicted.append(predicted_anomaly)

        metrics = calculate_metrics(actual, predicted)

        print("\n=== AEGIS FRAUD DETECTION EVALUATION ===")
        print(f"Historical transactions: {len(history)}")
        print(f"Evaluation cases: {len(cases)}")
        print(f"Decision threshold: {THRESHOLD}/100")
        print("\nConfusion matrix:")
        print(f"True positives:  {metrics['TP']}")
        print(f"True negatives:  {metrics['TN']}")
        print(f"False positives: {metrics['FP']}")
        print(f"False negatives: {metrics['FN']}")

        print("\nMetrics:")
        print(f"Precision:           {metrics['precision']:.2%}")
        print(f"Recall:              {metrics['recall']:.2%}")
        print(f"F1-score:            {metrics['f1']:.2%}")
        print(
            f"False-positive rate: "
            f"{metrics['false_positive_rate']:.2%}"
        )

        print(
            "\nNOTE: This is a controlled synthetic test, "
            "not evidence of real-world fraud detection accuracy."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()