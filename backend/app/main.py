from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routers.products import router as products_router
from app.routers.customer import router as customer_router
from app.routers.bill import router as bill_router
from app.routers.settings import router as settings_router
from app.routers.backup import router as backup_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SimpleDigitalKhata API",
    description="Backend API for SimpleDigitalKhata",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)
app.include_router(customer_router)
app.include_router(bill_router)
app.include_router(settings_router)
app.include_router(backup_router)

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