
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

from app.services.ml_anomaly_detection import analyze_ml_anomaly


BASE_TIME = datetime(2026, 10, 27, 15, 0, 0)


def make_transaction(
    customer_id,
    amount,
    timestamp,
    status="completed",
    location="Delhi",
):
    return SimpleNamespace(
        id=uuid4(),
        transaction_reference=f"TEST-{uuid4().hex[:10]}",
        customer_id=customer_id,
        amount=float(amount),
        currency="INR",
        transaction_type="purchase",
        payment_method="card",
        status=status,
        location=location,
        transaction_time=timestamp,
    )


def make_history(customer_id, amounts, base_time=BASE_TIME):
    history = []

    for index, amount in enumerate(amounts):
        history.append(
            make_transaction(
                customer_id,
                amount,
                base_time - timedelta(days=len(amounts) - index),
            )
        )

    return history


class FraudDetectionTests(unittest.TestCase):

    def analyse(self, transaction, history):
        return analyze_ml_anomaly(
            transaction=transaction,
            db=None,
            history=history,
        )

    def test_routine_purchase_has_low_score(self):
        customer = "CUSTOMER-NORMAL"
        history = make_history(
            customer,
            [650, 700, 750, 800, 850, 900, 700, 800, 750, 850, 900, 700],
        )
        transaction = make_transaction(customer, 800, BASE_TIME)

        result = self.analyse(transaction, history)

        self.assertTrue(result["ml_available"])
        self.assertLess(result["anomaly_score"], 40)
        self.assertFalse(result["is_anomaly"])

    def test_declined_transaction_is_flagged(self):
        customer = "CUSTOMER-DECLINED"
        history = make_history(
            customer,
            [700, 800, 850, 900, 750, 800, 950, 700, 850, 900, 800, 750],
        )
        transaction = make_transaction(
            customer, 900, BASE_TIME, status="declined"
        )

        result = self.analyse(transaction, history)

        self.assertGreaterEqual(result["anomaly_score"], 40)
        self.assertTrue(result["is_anomaly"])
        self.assertTrue(
            any("status" in reason.lower() for reason in result["reasons"])
        )

    def test_customer_spending_spike_is_flagged(self):
        customer = "CUSTOMER-SPIKE"
        history = make_history(
            customer,
            [250, 300, 350, 400, 250, 300, 350, 450, 300, 250, 400, 350],
        )
        transaction = make_transaction(customer, 15000, BASE_TIME)

        result = self.analyse(transaction, history)

        self.assertGreaterEqual(result["anomaly_score"], 40)
        self.assertTrue(result["is_anomaly"])

    def test_repeated_transactions_are_flagged(self):
        customer = "CUSTOMER-REPEAT"
        history = make_history(
            customer,
            [250, 300, 350, 300, 250, 400, 300, 350, 250, 300, 350, 300],
        )

        for minutes_ago, amount in [(45, 200), (25, 250), (10, 275)]:
            history.append(
                make_transaction(
                    customer,
                    amount,
                    BASE_TIME - timedelta(minutes=minutes_ago),
                )
            )

        transaction = make_transaction(customer, 300, BASE_TIME)
        result = self.analyse(transaction, history)

        self.assertGreaterEqual(result["anomaly_score"], 40)
        self.assertTrue(result["is_anomaly"])
        self.assertGreaterEqual(
            result["features"]["recent_customer_transaction_count"], 3
        )

    def test_insufficient_history_returns_unavailable(self):
        customer = "CUSTOMER-NEW"
        history = make_history(customer, [100, 200, 300])
        transaction = make_transaction(customer, 150, BASE_TIME)

        result = self.analyse(transaction, history)

        self.assertFalse(result["ml_available"])
        self.assertIsNone(result["anomaly_score"])

    def test_score_is_bounded_and_not_a_probability(self):
        customer = "CUSTOMER-MULTIPLE-SIGNALS"
        history = make_history(
            customer,
            [500, 650, 700, 800, 600, 750, 500, 650, 700, 600, 800, 550],
        )
        transaction = make_transaction(
            customer,
            30000,
            BASE_TIME.replace(hour=3),
            status="declined",
            location=None,
        )

        result = self.analyse(transaction, history)

        self.assertGreaterEqual(result["anomaly_score"], 0)
        self.assertLessEqual(result["anomaly_score"], 100)
        self.assertTrue(result["is_anomaly"])
        self.assertIn("not a trained", result["note"].lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
