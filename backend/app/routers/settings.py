from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.shop_settings import ShopSettings
from app.schemas.settings import (
    ShopSettingsResponse,
    ShopSettingsUpdate,
)


router = APIRouter(
    prefix="/api/settings",
    tags=["Settings"],
)


@router.get(
    "",
    response_model=ShopSettingsResponse,
)
def get_settings(
    db: Session = Depends(get_db),
):
    settings = db.scalar(
        select(ShopSettings).limit(1)
    )

    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop settings not found.",
        )

    return settings


@router.put(
    "",
    response_model=ShopSettingsResponse,
)
def update_settings(
    settings_data: ShopSettingsUpdate,
    db: Session = Depends(get_db),
):
    settings = db.scalar(
        select(ShopSettings).limit(1)
    )

    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop settings not found.",
        )

    settings.shop_name = settings_data.shop_name
    settings.phone = settings_data.phone
    settings.address = settings_data.address
    settings.logo_url = settings_data.logo_url

    db.commit()
    db.refresh(settings)

    return settings