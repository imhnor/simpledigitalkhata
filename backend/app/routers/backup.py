from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.bill import Bill
from app.models.bill_item import BillItem
from app.models.customer import Customer
from app.models.product import Product
from app.models.shop_settings import ShopSettings
from app.schemas.backup import BackupData

router = APIRouter(
    prefix="/api/backup",
    tags=["Backup"],
)


@router.get("/export")
def export_backup(
    db: Session = Depends(get_db),
):
    products = db.scalars(
        select(Product).order_by(Product.name)
    ).all()

    customers = db.scalars(
        select(Customer).order_by(Customer.name)
    ).all()

    bills = db.scalars(
        select(Bill).order_by(Bill.created_at)
    ).all()

    bill_items = db.scalars(
        select(BillItem)
    ).all()

    shop_settings = db.scalars(
        select(ShopSettings)
    ).all()

    backup_data = {
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),

        "products": [
            {
                "id": str(product.id),
                "name": product.name,
                "barcode": product.barcode,
                "price": str(product.price),
                "stock_quantity": product.stock_quantity,
            }
            for product in products
        ],

        "customers": [
            {
                "id": str(customer.id),
                "name": customer.name,
                "phone": customer.phone,
            }
            for customer in customers
        ],

        "bills": [
            {
                "id": str(bill.id),
                "bill_number": bill.bill_number,
                "customer_id": (
                    str(bill.customer_id)
                    if bill.customer_id
                    else None
                ),
                "total": str(bill.total),
                "payment_status": bill.payment_status,
                "created_at": bill.created_at.isoformat(),
                "updated_at": bill.updated_at.isoformat(),
            }
            for bill in bills
        ],

        "bill_items": [
            {
                "id": str(item.id),
                "bill_id": str(item.bill_id),
                "product_id": (
                    str(item.product_id)
                    if item.product_id
                    else None
                ),
                "product_name": item.product_name,
                "barcode": item.barcode,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "total": str(item.total),
            }
            for item in bill_items
        ],

        "shop_settings": [
            {
                "id": str(settings.id),
                "shop_name": settings.shop_name,
                "phone": settings.phone,
                "address": settings.address,
                "logo_url": settings.logo_url,
            }
            for settings in shop_settings
        ],
    }

    return JSONResponse(content=backup_data)




@router.post("/validate")
async def validate_backup(
    file: UploadFile = File(...),
):
    if file.content_type != "application/json":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backup file must be a JSON file.",
        )

    try:
        file_content = await file.read()
        backup_data = BackupData.model_validate_json(file_content)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid backup JSON or backup structure.",
        )

    if backup_data.version != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported backup version.",
        )

    product_ids = [product.id for product in backup_data.products]
    customer_ids = [customer.id for customer in backup_data.customers]
    bill_ids = [bill.id for bill in backup_data.bills]
    bill_item_ids = [item.id for item in backup_data.bill_items]

    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate product IDs found in backup.",
        )

    if len(customer_ids) != len(set(customer_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate customer IDs found in backup.",
        )

    if len(bill_ids) != len(set(bill_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate bill IDs found in backup.",
        )

    if len(bill_item_ids) != len(set(bill_item_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate bill item IDs found in backup.",
        )

    customer_id_set = set(customer_ids)
    product_id_set = set(product_ids)
    bill_id_set = set(bill_ids)

    for bill in backup_data.bills:
        if bill.customer_id is not None:
            if bill.customer_id not in customer_id_set:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Bill '{bill.bill_number}' references "
                        "a customer that does not exist in the backup."
                    ),
                )

    for item in backup_data.bill_items:
        if item.bill_id not in bill_id_set:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Bill item '{item.id}' references "
                    "a bill that does not exist in the backup."
                ),
            )

        if item.product_id is not None:
            if item.product_id not in product_id_set:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Bill item '{item.id}' references "
                        "a product that does not exist in the backup."
                    ),
                )

    return {
        "valid": True,
        "message": "Backup file is valid.",
        "version": backup_data.version,
        "counts": {
            "products": len(backup_data.products),
            "customers": len(backup_data.customers),
            "bills": len(backup_data.bills),
            "bill_items": len(backup_data.bill_items),
            "shop_settings": len(backup_data.shop_settings),
        },
    }

@router.post("/restore")
async def restore_backup(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if file.content_type != "application/json":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backup file must be a JSON file.",
        )

    try:
        file_content = await file.read()
        backup_data = BackupData.model_validate_json(file_content)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid backup JSON or backup structure.",
        )

    if backup_data.version != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported backup version.",
        )

    # -----------------------------------
    # Validate IDs and relationships
    # -----------------------------------

    product_ids = [product.id for product in backup_data.products]
    customer_ids = [customer.id for customer in backup_data.customers]
    bill_ids = [bill.id for bill in backup_data.bills]
    bill_item_ids = [item.id for item in backup_data.bill_items]

    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate product IDs found in backup.",
        )

    if len(customer_ids) != len(set(customer_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate customer IDs found in backup.",
        )

    if len(bill_ids) != len(set(bill_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate bill IDs found in backup.",
        )

    if len(bill_item_ids) != len(set(bill_item_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate bill item IDs found in backup.",
        )

    product_id_set = set(product_ids)
    customer_id_set = set(customer_ids)
    bill_id_set = set(bill_ids)

    for bill in backup_data.bills:
        if bill.customer_id is not None:
            if bill.customer_id not in customer_id_set:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Bill '{bill.bill_number}' references "
                        "a customer that does not exist in the backup."
                    ),
                )

    for item in backup_data.bill_items:
        if item.bill_id not in bill_id_set:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Bill item '{item.id}' references "
                    "a bill that does not exist in the backup."
                ),
            )

        if item.product_id is not None:
            if item.product_id not in product_id_set:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Bill item '{item.id}' references "
                        "a product that does not exist in the backup."
                    ),
                )

    # -----------------------------------
    # Database restore transaction
    # -----------------------------------

    try:
        # Delete dependent data first.
        db.execute(delete(BillItem))
        db.execute(delete(Bill))

        # Customers and products can now be deleted.
        db.execute(delete(Customer))
        db.execute(delete(Product))
        db.execute(delete(ShopSettings))

        db.flush()

        # -----------------------------------
        # Restore Products
        # -----------------------------------

        for product_data in backup_data.products:
            product = Product(
                id=product_data.id,
                name=product_data.name,
                barcode=product_data.barcode,
                price=product_data.price,
                stock_quantity=product_data.stock_quantity,
            )

            db.add(product)

        db.flush()

        # -----------------------------------
        # Restore Customers
        # -----------------------------------

        for customer_data in backup_data.customers:
            customer = Customer(
                id=customer_data.id,
                name=customer_data.name,
                phone=customer_data.phone,
            )

            db.add(customer)

        db.flush()

        # -----------------------------------
        # Restore Shop Settings
        # -----------------------------------

        for settings_data in backup_data.shop_settings:
            settings = ShopSettings(
                id=settings_data.id,
                shop_name=settings_data.shop_name,
                phone=settings_data.phone,
                address=settings_data.address,
                logo_url=settings_data.logo_url,
            )

            db.add(settings)

        db.flush()

        # -----------------------------------
        # Restore Bills
        # -----------------------------------

        for bill_data in backup_data.bills:
            bill = Bill(
                id=bill_data.id,
                bill_number=bill_data.bill_number,
                customer_id=bill_data.customer_id,
                total=bill_data.total,
                payment_status=bill_data.payment_status,
                created_at=bill_data.created_at,
                updated_at=bill_data.updated_at,
            )

            db.add(bill)

        db.flush()

        # -----------------------------------
        # Restore Bill Items
        # -----------------------------------

        for item_data in backup_data.bill_items:
            bill_item = BillItem(
                id=item_data.id,
                bill_id=item_data.bill_id,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                barcode=item_data.barcode,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                total=item_data.total,
            )

            db.add(bill_item)

        db.flush()

        # -----------------------------------
        # Reset bill number sequence
        # -----------------------------------

        db.execute(
            text(
                """
                SELECT setval(
                    'bill_number_seq',
                    COALESCE(
                        (
                            SELECT MAX(
                                CAST(
                                    SUBSTRING(bill_number FROM 3)
                                    AS BIGINT
                                )
                            )
                            FROM bills
                            WHERE bill_number ~ '^B-[0-9]+$'
                        ),
                        0
                    )
                )
                """
            )
        )

        # -----------------------------------
        # Commit everything
        # -----------------------------------

        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backup could not be restored because it violates database constraints.",
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backup restore failed. No changes were applied.",
        )

    return {
        "success": True,
        "message": "Backup restored successfully.",
        "counts": {
            "products": len(backup_data.products),
            "customers": len(backup_data.customers),
            "bills": len(backup_data.bills),
            "bill_items": len(backup_data.bill_items),
            "shop_settings": len(backup_data.shop_settings),
        },
    }