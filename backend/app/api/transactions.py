
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionResponse

from fastapi import UploadFile, File
from fastapi.responses import JSONResponse

from app.services.csv_ingestion import import_transactions

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
):
    transaction = Transaction(**payload.model_dump())
    db.add(transaction)

    try:
        db.commit()
        db.refresh(transaction)
        return transaction
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A transaction with this reference already exists.",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the transaction.",
        )


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    statement = (
        select(Transaction)
        .order_by(Transaction.transaction_time.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(statement).all()


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
):
    from uuid import UUID

    try:
        parsed_id = UUID(transaction_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction ID.",
        )

    transaction = db.get(Transaction, parsed_id)

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )

    db.delete(transaction)
    db.commit()


@router.post("/import-csv", tags=["Data Ingestion"])
def upload_transactions_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a .csv file.",
        )

    content = file.file.read()

    print("CSV filename:", file.filename)
    print("CSV byte count:", len(content))
    print("CSV preview:", repr(content[:200]))

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded CSV file is empty.",
        )

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="CSV file must be 10 MB or smaller.",
        )

    try:
        result = import_transactions(content, db)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during CSV import.",
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result,
    )

