from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    barcode: str | None = Field(
        default=None,
        max_length=100,
    )

    price: Decimal = Field(
        ...,
        ge=0,
        decimal_places=2,
        max_digits=12,
    )

    stock_quantity: int = Field(
        default=0,
        ge=0,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = " ".join(value.split())

        if not value:
            raise ValueError("Product name cannot be empty.")

        return value

    @field_validator("barcode")
    @classmethod
    def validate_barcode(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return value


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    barcode: str | None = Field(
        default=None,
        max_length=100,
    )

    price: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        max_digits=12,
    )

    stock_quantity: int | None = Field(
        default=None,
        ge=0,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = " ".join(value.split())

        if not value:
            raise ValueError("Product name cannot be empty.")

        return value

    @field_validator("barcode")
    @classmethod
    def validate_barcode(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return value


class ProductResponse(ProductBase):
    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )