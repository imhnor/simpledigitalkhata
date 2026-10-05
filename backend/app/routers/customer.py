from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.customer import Customer
from app.schemas.customer import (
    CustomerBillHistoryItem,
    CustomerCreate,
    CustomerResponse,
    CustomerSummary,
    CustomerUpdate,
)


router = APIRouter(
    prefix="/api/customers",
    tags=["Customers"],
)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
):
    name = customer_data.name.strip()

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer name cannot be empty.",
        )

    phone = (
        customer_data.phone.strip()
        if customer_data.phone is not None
        else None
    )

    customer = Customer(
        name=name,
        phone=phone,
    )

    db.add(customer)

    try:
        db.commit()
        db.refresh(customer)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A customer with this name already exists.",
        )

    return customer


@router.get(
    "",
    response_model=list[CustomerResponse],
)
def get_customers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    statement = (
        select(Customer)
        .order_by(Customer.name.asc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


@router.get(
    "/search",
    response_model=list[CustomerResponse],
)
def search_customers(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    search_value = f"%{q.strip()}%"

    statement = (
        select(Customer)
        .where(
            or_(
                Customer.name.ilike(search_value),
                Customer.phone.ilike(search_value),
            )
        )
        .order_by(Customer.name.asc())
        .limit(limit)
    )

    return list(db.scalars(statement).all())


@router.get(
    "/{customer_id}/summary",
    response_model=CustomerSummary,
)
def get_customer_summary(
    customer_id: UUID,
    db: Session = Depends(get_db),
):
    customer_exists = db.scalar(
        select(Customer.id).where(Customer.id == customer_id)
    )

    if customer_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    statement = text(
        """
        SELECT
            c.id AS customer_id,
            c.name AS customer_name,
            COUNT(b.id) AS total_bills,
            COUNT(*) FILTER (
                WHERE b.payment_status = 'paid'
            ) AS paid_bills,
            COUNT(*) FILTER (
                WHERE b.payment_status = 'not_paid'
            ) AS not_paid_bills,
            COALESCE(
                SUM(b.total) FILTER (
                    WHERE b.payment_status = 'not_paid'
                ),
                0
            ) AS unpaid_total
        FROM customers c
        LEFT JOIN bills b
            ON c.id = b.customer_id
        WHERE c.id = :customer_id
        GROUP BY c.id, c.name
        """
    )

    result = db.execute(
        statement,
        {"customer_id": customer_id},
    ).mappings().one()

    return result


@router.get(
    "/{customer_id}/bills",
    response_model=list[CustomerBillHistoryItem],
)
def get_customer_bill_history(
    customer_id: UUID,
    db: Session = Depends(get_db),
):
    customer_exists = db.scalar(
        select(Customer.id).where(Customer.id == customer_id)
    )

    if customer_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    statement = text(
        """
        SELECT
            bill_number,
            created_at,
            total,
            payment_status
        FROM bills
        WHERE customer_id = :customer_id
        ORDER BY created_at DESC
        """
    )

    result = db.execute(
        statement,
        {"customer_id": customer_id},
    ).mappings().all()

    return result


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
):
    customer = db.scalar(
        select(Customer).where(Customer.id == customer_id)
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    return customer


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def update_customer(
    customer_id: UUID,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
):
    customer = db.scalar(
        select(Customer).where(Customer.id == customer_id)
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    update_data = customer_data.model_dump(exclude_unset=True)

    if "name" in update_data:
        name = update_data["name"].strip()

        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer name cannot be empty.",
            )

        customer.name = name

    if "phone" in update_data:
        phone = update_data["phone"]

        customer.phone = (
            phone.strip()
            if phone is not None
            else None
        )

    try:
        db.commit()
        db.refresh(customer)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A customer with this name already exists.",
        )

    return customer