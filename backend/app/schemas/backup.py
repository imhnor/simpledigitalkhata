from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BackupProduct(BaseModel):
    id: UUID
    name: str
    barcode: str | None
    price: Decimal
    stock_quantity: int


class BackupCustomer(BaseModel):
    id: UUID
    name: str
    phone: str | None


class BackupBill(BaseModel):
    id: UUID
    bill_number: str
    customer_id: UUID | None
    total: Decimal
    payment_status: str
    created_at: datetime
    updated_at: datetime


class BackupBillItem(BaseModel):
    id: UUID
    bill_id: UUID
    product_id: UUID | None
    product_name: str
    barcode: str | None
    quantity: int
    unit_price: Decimal
    total: Decimal


class BackupShopSettings(BaseModel):
    id: UUID
    shop_name: str
    phone: str | None
    address: str | None
    logo_url: str | None


class BackupData(BaseModel):
    version: int
    exported_at: datetime

    products: list[BackupProduct]
    customers: list[BackupCustomer]
    bills: list[BackupBill]
    bill_items: list[BackupBillItem]
    shop_settings: list[BackupShopSettings]