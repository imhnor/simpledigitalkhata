from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routers.products import router as products_router
from app.routers.customer import router as customer_router

app = FastAPI(
    title="SimpleDigitalKhata API",
    description="Backend API for SimpleDigitalKhata",
    version="1.0.0",
)


app.include_router(products_router)
app.include_router(customer_router)



@app.get("/")
def root():
    return {
        "message": "SimpleDigitalKhata API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "SimpleDigitalKhata API",
    }


@app.get("/health/db")
def database_health_check(
    db: Session = Depends(get_db),
):
    try:
        result = db.execute(
            text("SELECT current_database()")
        )

        database_name = result.scalar()

        return {
            "status": "ok",
            "database": "connected",
            "database_name": database_name,
        }

    except Exception as error:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(error),
        }