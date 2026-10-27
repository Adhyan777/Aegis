
import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


REQUIRED_COLUMNS = {
    "transaction_reference",
    "customer_id",
    "amount",
    "currency",
    "transaction_type",
    "payment_method",
    "status",
    "location",
    "transaction_time",
}


def import_transactions(file_content: bytes, db: Session) -> dict:
    """Validate and import transactions from a UTF-8 CSV file."""

    try:
        text = file_content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return {
            "imported": 0,
            "skipped": 0,
            "errors": ["File must use UTF-8 encoding."],
        }

    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff\r\n")))

    if not reader.fieldnames:
        return {
            "imported": 0,
            "skipped": 0,
            "errors": ["CSV file is empty or has no header row."],
        }

    reader.fieldnames = [
        name.strip() if name else ""
        for name in reader.fieldnames
    ]

    missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)

    if missing_columns:
        return {
            "imported": 0,
            "skipped": 0,
            "errors": [
                "Missing required columns: "
                + ", ".join(sorted(missing_columns))
            ],
        }

    imported = 0
    skipped = 0
    errors = []
    seen_references = set()

    for row_number, row in enumerate(reader, start=2):
        try:
            if None in row:
                raise ValueError("Row contains extra CSV columns.")

            row = {
                key.strip(): (value.strip() if value else "")
                for key, value in row.items()
                if key is not None
            }

            reference = row["transaction_reference"]

            if not reference:
                raise ValueError("Transaction reference is required.")

            if reference in seen_references:
                raise ValueError(
                    f"Duplicate reference '{reference}' in this file."
                )

            seen_references.add(reference)

            if db.query(Transaction).filter_by(
                transaction_reference=reference
            ).first():
                raise ValueError(
                    f"Reference '{reference}' already exists in the database."
                )

            amount = Decimal(row["amount"])

            if not amount.is_finite() or amount <= 0:
                raise ValueError("Amount must be a positive finite number.")

            if amount.as_tuple().exponent < -2:
                raise ValueError("Amount can have at most 2 decimal places.")

            if len(row["currency"]) != 3:
                raise ValueError("Currency must contain 3 characters.")

            if not row["customer_id"]:
                raise ValueError("Customer ID is required.")

            if not row["transaction_type"]:
                raise ValueError("Transaction type is required.")

            if not row["payment_method"]:
                raise ValueError("Payment method is required.")

            if not row["status"]:
                raise ValueError("Status is required.")

            if len(reference) > 100:
                raise ValueError("Transaction reference is too long.")

            if len(row["customer_id"]) > 100:
                raise ValueError("Customer ID is too long.")

            if len(row["currency"]) > 3:
                raise ValueError("Currency must contain 3 characters.")

            if len(row["transaction_type"]) > 50:
                raise ValueError("Transaction type is too long.")

            if len(row["payment_method"]) > 50:
                raise ValueError("Payment method is too long.")

            if len(row["status"]) > 30:
                raise ValueError("Status is too long.")

            if len(row["location"]) > 150:
                raise ValueError("Location is too long.")

            transaction_time = datetime.fromisoformat(
                row["transaction_time"].replace("Z", "+00:00")
            )

            if transaction_time.tzinfo is None:
                raise ValueError(
                    "Transaction time must include a timezone offset."
                )

            transaction = Transaction(
                transaction_reference=reference,
                customer_id=row["customer_id"],
                amount=amount,
                currency=row["currency"].upper(),
                transaction_type=row["transaction_type"],
                payment_method=row["payment_method"],
                status=row["status"],
                location=row["location"] or None,
                transaction_time=transaction_time,
            )

            db.add(transaction)
            db.flush()
            imported += 1

        except (ValueError, KeyError, InvalidOperation) as exc:
            db.rollback()
            imported = 0
            skipped += 1
            errors.append(f"Row {row_number}: {exc}")
            # Earlier valid rows were rolled back, so reprocess is needed.
            return {
                "imported": 0,
                "skipped": skipped,
                "errors": errors
                + ["Import stopped to avoid a partial import."],
            }

        except IntegrityError:
            db.rollback()
            return {
                "imported": 0,
                "skipped": skipped + 1,
                "errors": [
                    f"Row {row_number}: duplicate or invalid database record."
                ],
            }

        except SQLAlchemyError:
            db.rollback()
            raise

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    }
