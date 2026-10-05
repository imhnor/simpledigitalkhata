from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BillItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(
        ...,
        gt=0,
    )


class BillCreate(BaseModel):
    customer_id: UUID | None = None

    items: list[BillItemCreate] = Field(
        ...,
        min_length=1,
    )

    payment_status: str = Field(
        default="not_paid",
    )


class BillItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID | None
    product_name: str
    barcode: str | None
    quantity: int
    unit_price: Decimal
    total: Decimal


class BillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    bill_number: str
    customer_id: UUID | None
    total: Decimal
    payment_status: str
    created_at: datetime
    updated_at: datetime


class BillDetailResponse(BillResponse):
    items: list[BillItemResponse]


class BillPaymentUpdate(BaseModel):
    payment_status: str