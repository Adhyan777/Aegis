
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    transaction_reference: str = Field(min_length=1, max_length=100)
    customer_id: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    transaction_type: str = Field(min_length=1, max_length=50)
    payment_method: str = Field(min_length=1, max_length=50)
    status: str = Field(default="completed", max_length=30)
    location: str | None = Field(default=None, max_length=150)
    transaction_time: datetime


class TransactionResponse(BaseModel):
    id: UUID
    transaction_reference: str
    customer_id: str
    amount: Decimal
    currency: str
    transaction_type: str
    payment_method: str
    status: str
    location: str | None
    transaction_time: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
