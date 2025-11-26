# 1. Set up env
-  Create backend folder
    mkdir backend
    cd backend
-  Create a virtualenv for the backend
    python -m venv .venv
- Activate it
    source .venv/bin/activate   # on macOS/Linux

# 2. Packages - PIP
fastapi[all] → FastAPI + Uvicorn server
sqlalchemy → ORM + table/models
psycopg2-binary → Postgres driver
python-dotenv → load .env file for DB URL later