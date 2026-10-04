from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db


app = FastAPI(
    title="SimpleDigitalKhata API",
    description="Backend API for SimpleDigitalKhata",
    version="1.0.0",
)


# --------------------------------------------------
# Root
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "SimpleDigitalKhata API is running"
    }


# --------------------------------------------------
# Application Health Check
# --------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "SimpleDigitalKhata API",
    }


# --------------------------------------------------
# Database Health Check
# --------------------------------------------------

@app.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }

    except Exception:
        return {
            "status": "error",
            "database": "disconnected",
        }