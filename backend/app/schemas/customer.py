from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CustomerCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )


class CustomerUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    phone: str | None


class CustomerBillHistoryItem(BaseModel):
    bill_number: str
    created_at: datetime
    total: Decimal
    payment_status: str


class CustomerSummary(BaseModel):
    customer_id: UUID
    customer_name: str
    total_bills: int
    paid_bills: int
    not_paid_bills: int
    unpaid_total: Decimal