# SIMPLE DIGITAL KHATA — BACKEND SETUP

## 1. Navigate to Backend

```powershell
cd backend
```

## 2. Create Virtual Environment

```powershell
python -m venv venv
```

## 3. Activate Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1
```

If activation is successful, the terminal should show:

```text
(venv)
```

## 4. Install Backend Dependencies

```powershell
pip install fastapi "uvicorn[standard]" sqlalchemy psycopg pydantic-settings python-dotenv python-multipart
```

These packages are used for:

* `fastapi` → REST API framework
* `uvicorn[standard]` → ASGI server
* `sqlalchemy` → Database ORM
* `psycopg` → PostgreSQL database driver
* `pydantic-settings` → `.env` configuration
* `python-dotenv` → Environment variable support
* `python-multipart` → File uploads and multipart/form-data

## 5. Start FastAPI Development Server

```powershell
uvicorn app.main:app --reload
```

Backend will run at:

```text
http://127.0.0.1:8000
```

## 6. API Documentation

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## 7. Health Checks

API health:

```text
GET /health
```

Database health:

```text
GET /health/db
```

Expected responses:

```json
{
  "status": "ok",
  "service": "Simple Digital Khata API"
}
```

and:

```json
{
  "status": "ok",
  "database": "connected"
}
```

## 8. Backend Environment File

Create:

```text
backend/.env
```

Example:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/simpledigitalkhata
```

Never commit the actual `.env` file to GitHub.

Create a safe example file:

```text
backend/.env.example
```

with:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/simpledigitalkhata
```

## 9. Backend Project Structure

```text
backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── database.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── product.py
│   │   ├── customer.py
│   │   ├── bill.py
│   │   ├── bill_item.py
│   │   └── shop_settings.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── product.py
│   │   ├── customer.py
│   │   ├── bill.py
│   │   ├── settings.py
│   │   └── backup.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── product.py
│   │   ├── customer.py
│   │   ├── bill.py
│   │   ├── settings.py
│   │   └── backup.py
│   │
│   └── services/
│       ├── __init__.py
│       └── bill_service.py
│
├── .env
├── .env.example
└── requirements.txt
```

## 10. Generate Requirements File

After installing all dependencies:

```powershell
pip freeze > requirements.txt
```

This allows the backend environment to be reproduced later.

## 11. Run Backend Again

Whenever you open the project again:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

## 12. Backend Verification Checklist

```text
BACKEND
[✓] Python environment
[✓] Virtual environment
[✓] Dependencies
[✓] Environment variables
[✓] PostgreSQL connection
[✓] FastAPI application
[✓] Uvicorn server
[✓] Swagger documentation
[✓] ReDoc documentation

API MODULES
[✓] Products
[✓] Customers
[✓] Bills
[✓] Shop Settings
[✓] Backup Export
[✓] Backup Validation
[✓] Backup Restore

SECURITY
[✓] .env protected
[✓] .gitignore
[✓] CORS
[✓] Safe error handling

DATABASE
[✓] PostgreSQL
[✓] Tables
[✓] Constraints
[✓] Indexes
[✓] Dummy data
[✓] Bill number sequence
[✓] Updated-at trigger

TESTING
[ ] Complete Swagger API testing
[ ] Edge-case testing
[ ] Transaction rollback testing
[ ] Stock deduction testing
[ ] Frontend integration testing
```
