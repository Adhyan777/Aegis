from datetime import datetime, timedelta, timezone
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import select
from app.db.database import SessionLocal
from app.models.transaction import Transaction

random.seed(42)

TOTAL = 500
METHODS = ["upi", "credit_card", "debit_card", "net_banking", "wallet"]
LOCATIONS = ["Pune", "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai"]
STATUSES = ["completed", "completed", "completed", "pending", "failed"]
TYPES = ["purchase", "purchase", "purchase", "refund"]


def main():
    db = SessionLocal()

    try:
        existing_refs = set(
            db.scalars(
                select(Transaction.transaction_reference)
            ).all()
        )

        now = datetime.now(timezone.utc)
        created = 0

        for i in range(1, TOTAL + 1):
            reference = f"AEG-SYN-{i:04d}"

            if reference in existing_refs:
                continue

            suspicious = random.random() < 0.10

            if suspicious:
                amount = round(random.uniform(10000, 50000), 2)
                status = random.choice(["failed", "declined", "completed"])
                hour = random.choice([0, 1, 2, 3, 4, 23])
                location = random.choice(LOCATIONS)
            else:
                amount = round(random.uniform(100, 5000), 2)
                status = random.choice(STATUSES)
                hour = random.randint(6, 22)
                location = random.choice(LOCATIONS)

            transaction_time = (
                now - timedelta(
                    days=random.randint(0, 90),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                )
            ).replace(
                hour=hour,
                minute=random.randint(0, 59),
                second=0,
                microsecond=0,
            )

            transaction = Transaction(
                transaction_reference=reference,
                customer_id=f"CUST-{random.randint(1, 100):03d}",
                amount=amount,
                currency="INR",
                transaction_type=(
                    "refund" if suspicious and random.random() < 0.25
                    else random.choice(TYPES)
                ),
                payment_method=random.choice(METHODS),
                status=status,
                location=location,
                transaction_time=transaction_time,
            )

            db.add(transaction)
            existing_refs.add(reference)
            created += 1

        db.commit()
        print(f"Successfully inserted {created} synthetic transactions.")
        print(f"Skipped existing references automatically.")
        print(f"Total transactions now: {db.query(Transaction).count()}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
