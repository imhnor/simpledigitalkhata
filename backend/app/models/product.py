import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    barcode: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    stock_quantity: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    __table_args__ = (
        CheckConstraint(
            "price >= 0",
            name="ck_products_price_non_negative",
        ),
        CheckConstraint(
            "stock_quantity >= 0",
            name="ck_products_stock_non_negative",
        ),
    )