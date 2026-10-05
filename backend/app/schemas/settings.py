from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ShopSettingsUpdate(BaseModel):
    shop_name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = None
    logo_url: str | None = None

    @field_validator("shop_name")
    @classmethod
    def validate_shop_name(cls, value: str) -> str:
        value = " ".join(value.split())

        if not value:
            raise ValueError("Shop name cannot be empty.")

        return value

    @field_validator("phone", "address", "logo_url")
    @classmethod
    def clean_optional_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class ShopSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shop_name: str
    phone: str | None
    address: str | None
    logo_url: str | None