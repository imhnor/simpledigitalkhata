from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.bill import Bill
from app.models.bill_item import BillItem
from app.models.product import Product
from app.schemas.bill import BillCreate


def create_bill(
    db: Session,
    bill_data: BillCreate,
) -> Bill:

    if bill_data.payment_status not in {
        "paid",
        "not_paid",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment status.",
        )

    if bill_data.customer_id is not None:
        customer_exists = db.execute(
            text(
                """
                SELECT id
                FROM customers
                WHERE id = :customer_id
                """
            ),
            {
                "customer_id": bill_data.customer_id,
            },
        ).scalar_one_or_none()

        if customer_exists is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found.",
            )

    product_ids = [
        item.product_id
        for item in bill_data.items
    ]

    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A product cannot appear more than once in a bill.",
        )

    products = (
        db.query(Product)
        .filter(Product.id.in_(product_ids))
        .with_for_update()
        .all()
    )

    products_by_id = {
        product.id: product
        for product in products
    }

    if len(products_by_id) != len(product_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more products were not found.",
        )

    bill_items = []
    bill_total = Decimal("0.00")

    for requested_item in bill_data.items:

        product = products_by_id[requested_item.product_id]

        if product.stock_quantity < requested_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock for "
                    f"'{product.name}'. "
                    f"Available: {product.stock_quantity}, "
                    f"requested: {requested_item.quantity}."
                ),
            )

        item_total = (
            product.price *
            requested_item.quantity
        )

        bill_total += item_total

        bill_items.append(
            {
                "product": product,
                "quantity": requested_item.quantity,
                "total": item_total,
            }
        )

    bill_number = db.execute(
        text(
            """
            SELECT 'B-' || LPAD(
                nextval('bill_number_seq')::text,
                6,
                '0'
            )
            """
        )
    ).scalar_one()

    bill = Bill(
        bill_number=bill_number,
        customer_id=bill_data.customer_id,
        total=bill_total,
        payment_status=bill_data.payment_status,
    )

    db.add(bill)
    db.flush()

    for item in bill_items:

        product = item["product"]
        quantity = item["quantity"]
        item_total = item["total"]

        bill_item = BillItem(
            bill_id=bill.id,
            product_id=product.id,
            product_name=product.name,
            barcode=product.barcode,
            quantity=quantity,
            unit_price=product.price,
            total=item_total,
        )

        db.add(bill_item)

        product.stock_quantity -= quantity

    db.flush()

    return bill