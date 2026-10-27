
from datetime import datetime, timedelta
from uuid import uuid4

from app.db.database import SessionLocal
from app.models.transaction import Transaction
from app.services.ml_anomaly_detection import analyze_ml_anomaly


THRESHOLD = 40


def normalize_datetime(value):
    """Convert timezone-aware datetimes to naive datetimes for comparisons."""
    if value is None:
        return None

    if value.tzinfo is not None:
        return value.replace(tzinfo=None)

    return value


def make_transaction(
    reference,
    customer_id,
    amount,
    transaction_time,
    status="completed",
    location="Delhi",
):
    return Transaction(
        id=uuid4(),
        transaction_reference=reference,
        customer_id=customer_id,
        amount=float(amount),
        currency="INR",
        transaction_type="purchase",
        payment_method="card",
        status=status,
        location=location,
        transaction_time=normalize_datetime(transaction_time),
    )


def add_profile(history, customer_id, amounts, test_time):
    """Build temporary historical transactions for a test customer."""
    for index, amount in enumerate(amounts):
        history.append(
            make_transaction(
                reference=f"STRESS-HIST-{uuid4().hex[:12]}",
                customer_id=customer_id,
                amount=amount,
                transaction_time=test_time
                - timedelta(days=len(amounts) - index),
            )
        )


def main():
    db = SessionLocal()

    try:
        database_history = (
            db.query(Transaction)
            .order_by(Transaction.transaction_time.asc())
            .all()
        )

        if len(database_history) < 10:
            print(
                "Need at least 10 existing transactions. "
                "Seed the database first."
            )
            return

        # Work on in-memory timestamps only; don't modify the database.
        for item in database_history:
            item.transaction_time = normalize_datetime(
                item.transaction_time
            )

        valid_times = [
            item.transaction_time
            for item in database_history
            if item.transaction_time is not None
        ]

        latest_time = max(valid_times, default=datetime.now())
        start = max(datetime.now(), latest_time) + timedelta(days=2)

        scenarios = [
            {
                "name": "Routine purchase",
                "customer": "STRESS-NORMAL",
                "amount": 800,
                "hour": 14,
                "status": "completed",
                "location": "Delhi",
                "profile": [
                    650, 700, 750, 800, 850, 900,
                    700, 800, 750, 850, 900, 700,
                ],
                "expected": "NORMAL",
            },
            {
                "name": "High amount, daytime, successful",
                "customer": "STRESS-HIGH-NORMAL",
                "amount": 13500,
                "hour": 14,
                "status": "completed",
                "location": "Delhi",
                "profile": [
                    11000, 12000, 12500, 13000, 14000, 12000,
                    13500, 12500, 13000, 14000, 11500, 13000,
                ],
                "expected": "REVIEW",
            },
            {
                "name": "Modest declined payment",
                "customer": "STRESS-DECLINED",
                "amount": 900,
                "hour": 13,
                "status": "declined",
                "location": "Delhi",
                "profile": [
                    700, 800, 850, 900, 750, 800,
                    950, 700, 850, 900, 800, 750,
                ],
                "expected": "SUSPICIOUS",
            },
            {
                "name": "Modest overnight payment",
                "customer": "STRESS-OVERNIGHT",
                "amount": 700,
                "hour": 2,
                "status": "completed",
                "location": "Delhi",
                "profile": [
                    600, 650, 700, 750, 800, 650,
                    700, 600, 750, 700, 650, 800,
                ],
                "expected": "REVIEW",
            },
            {
                "name": "Sudden spending spike",
                "customer": "STRESS-SPENDING-SPIKE",
                "amount": 15000,
                "hour": 15,
                "status": "completed",
                "location": "Delhi",
                "profile": [
                    250, 300, 350, 400, 250, 300,
                    350, 450, 300, 250, 400, 350,
                ],
                "expected": "SUSPICIOUS",
            },
            {
                "name": "Repeated transactions in one hour",
                "customer": "STRESS-REPEAT",
                "amount": 300,
                "hour": 16,
                "status": "completed",
                "location": "Delhi",
                "profile": [
                    250, 300, 350, 300, 250, 400,
                    300, 350, 250, 300, 350, 300,
                ],
                "repeat": True,
                "expected": "SUSPICIOUS",
            },
            {
                "name": "Large declined overnight payment",
                "customer": "STRESS-MULTI-SIGNAL",
                "amount": 30000,
                "hour": 3,
                "status": "declined",
                "location": "Delhi",
                "profile": [
                    500, 650, 700, 800, 600, 750,
                    500, 650, 700, 600, 800, 550,
                ],
                "expected": "SUSPICIOUS",
            },
            {
                "name": "Ordinary payment with missing location",
                "customer": "STRESS-MISSING-LOCATION",
                "amount": 700,
                "hour": 12,
                "status": "completed",
                "location": None,
                "profile": [
                    600, 700, 750, 650, 800, 700,
                    650, 750, 600, 700, 800, 650,
                ],
                "expected": "REVIEW",
            },
        ]

        results = []

        print(f"\nDatabase transactions: {len(database_history)}")
        print(f"Anomaly threshold: {THRESHOLD}/100")
        print("-" * 100)
        print(
            f"{'Scenario':39} {'Score':>7} "
            f"{'Prediction':>13} {'Expected':>13} {'Result':>10}"
        )
        print("-" * 100)

        for index, scenario in enumerate(scenarios):
            transaction_time = (
                start + timedelta(hours=index * 4)
            ).replace(
                hour=scenario["hour"],
                minute=15,
                second=0,
                microsecond=0,
            )

            # Copy records so this test doesn't alter the loaded objects.
            history = list(database_history)

            add_profile(
                history,
                scenario["customer"],
                scenario["profile"],
                transaction_time,
            )

            if scenario.get("repeat"):
                for minutes_ago, amount in [
                    (45, 200),
                    (25, 250),
                    (10, 275),
                ]:
                    history.append(
                        make_transaction(
                            reference=f"STRESS-REPEAT-{uuid4().hex[:8]}",
                            customer_id=scenario["customer"],
                            amount=amount,
                            transaction_time=transaction_time
                            - timedelta(minutes=minutes_ago),
                        )
                    )

            transaction = make_transaction(
                reference=f"STRESS-TEST-{index + 1:02d}",
                customer_id=scenario["customer"],
                amount=scenario["amount"],
                transaction_time=transaction_time,
                status=scenario["status"],
                location=scenario["location"],
            )

            analysis = analyze_ml_anomaly(
                transaction,
                db,
                history=history,
            )

            score = analysis.get("anomaly_score")
            available = analysis.get("ml_available", False)

            if not available or score is None:
                prediction = "UNAVAILABLE"
            elif score >= THRESHOLD:
                prediction = "SUSPICIOUS"
            else:
                prediction = "NORMAL"

            if scenario["expected"] == "REVIEW":
                outcome = "REVIEW"
            elif prediction == "UNAVAILABLE":
                outcome = "NO SCORE"
            else:
                outcome = (
                    "PASS"
                    if prediction == scenario["expected"]
                    else "MISS"
                )

            score_text = "N/A" if score is None else f"{score:.1f}"

            print(
                f"{scenario['name'][:39]:39} "
                f"{score_text:>7} "
                f"{prediction:>13} "
                f"{scenario['expected']:>13} "
                f"{outcome:>10}"
            )

            results.append(
                {
                    "name": scenario["name"],
                    "expected": scenario["expected"],
                    "prediction": prediction,
                    "score": score,
                    "outcome": outcome,
                }
            )

        clear_cases = [
            result
            for result in results
            if result["expected"] in ("NORMAL", "SUSPICIOUS")
            and result["prediction"] in ("NORMAL", "SUSPICIOUS")
        ]

        tp = sum(
            r["expected"] == "SUSPICIOUS"
            and r["prediction"] == "SUSPICIOUS"
            for r in clear_cases
        )
        tn = sum(
            r["expected"] == "NORMAL"
            and r["prediction"] == "NORMAL"
            for r in clear_cases
        )
        fp = sum(
            r["expected"] == "NORMAL"
            and r["prediction"] == "SUSPICIOUS"
            for r in clear_cases
        )
        fn = sum(
            r["expected"] == "SUSPICIOUS"
            and r["prediction"] == "NORMAL"
            for r in clear_cases
        )

        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0
        )
        false_positive_rate = fp / (fp + tn) if fp + tn else 0

        print("\n" + "=" * 48)
        print("STRESS-TEST SUMMARY")
        print("=" * 48)
        print(f"Clear-label cases scored: {len(clear_cases)}")
        print(f"True positives: {tp}")
        print(f"True negatives: {tn}")
        print(f"False positives: {fp}")
        print(f"False negatives: {fn}")
        print(f"Precision: {precision:.1%}")
        print(f"Recall: {recall:.1%}")
        print(f"F1 score: {f1:.1%}")
        print(f"False-positive rate: {false_positive_rate:.1%}")
        print(
            "Review cases: "
            f"{sum(r['expected'] == 'REVIEW' for r in results)}"
        )
        print(
            "\nThese are controlled synthetic scenarios, "
            "not real-world model metrics."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
