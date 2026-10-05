from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import Product
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
):
    product = Product(
        name=product_data.name,
        barcode=product_data.barcode,
        price=product_data.price,
        stock_quantity=product_data.stock_quantity,
    )

    db.add(product)

    try:
        db.commit()
        db.refresh(product)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this barcode already exists.",
        )

    return product


@router.get(
    "",
    response_model=list[ProductResponse],
)
def get_products(
    search: str | None = Query(
        default=None,
        description="Search by product name or barcode.",
    ),
    db: Session = Depends(get_db),
):
    statement = select(Product)

    if search:
        search_term = search.strip()

        if search_term:
            statement = statement.where(
                or_(
                    Product.name.ilike(f"%{search_term}%"),
                    Product.barcode.ilike(f"%{search_term}%"),
                )
            )

    statement = statement.order_by(Product.name.asc())

    products = db.scalars(statement).all()

    return products


@router.get(
    "/barcode/{barcode}",
    response_model=ProductResponse,
)
def get_product_by_barcode(
    barcode: str,
    db: Session = Depends(get_db),
):
    barcode = barcode.strip()

    if not barcode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Barcode cannot be empty.",
        )

    statement = select(Product).where(
        Product.barcode == barcode
    )

    product = db.scalar(statement)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    return product


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    return product


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    update_data = product_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(product, field, value)

    try:
        db.commit()
        db.refresh(product)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this barcode already exists.",
        )

    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    db.delete(product)
    db.commit()

    return None