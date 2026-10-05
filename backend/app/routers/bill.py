from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.bill import Bill
from app.models.bill_item import BillItem
from app.schemas.bill import (
    BillCreate,
    BillDetailResponse,
    BillPaymentUpdate,
    BillResponse,
)
from app.services.bill_service import create_bill


router = APIRouter(
    prefix="/api/bills",
    tags=["Bills"],
)


@router.post(
    "",
    response_model=BillResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_bill(
    bill_data: BillCreate,
    db: Session = Depends(get_db),
):
    try:
        bill = create_bill(
            db=db,
            bill_data=bill_data,
        )

        db.commit()
        db.refresh(bill)

        return bill

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create bill.",
        )


@router.get(
    "",
    response_model=list[BillResponse],
)
def get_bills(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    statement = (
        select(Bill)
        .order_by(Bill.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


@router.get(
    "/{bill_id}",
    response_model=BillDetailResponse,
)
def get_bill_detail(
    bill_id: UUID,
    db: Session = Depends(get_db),
):
    bill = db.scalar(
        select(Bill).where(Bill.id == bill_id)
    )

    if bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found.",
        )

    items = list(
        db.scalars(
            select(BillItem)
            .where(BillItem.bill_id == bill.id)
        ).all()
    )

    return BillDetailResponse(
        id=bill.id,
        bill_number=bill.bill_number,
        customer_id=bill.customer_id,
        total=bill.total,
        payment_status=bill.payment_status,
        created_at=bill.created_at,
        updated_at=bill.updated_at,
        items=items,
    )


@router.patch(
    "/{bill_id}/payment-status",
    response_model=BillResponse,
)
def update_payment_status(
    bill_id: UUID,
    payment_data: BillPaymentUpdate,
    db: Session = Depends(get_db),
):
    if payment_data.payment_status not in {
        "paid",
        "not_paid",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment status.",
        )

    bill = db.scalar(
        select(Bill).where(Bill.id == bill_id)
    )

    if bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found.",
        )

    bill.payment_status = payment_data.payment_status

    try:
        db.commit()
        db.refresh(bill)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update payment status.",
        )

    return bill