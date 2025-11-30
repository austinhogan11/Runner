FROM python:3.12-slim

WORKDIR /app

# System deps for psycopg2 / Postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code (including alembic.ini and alembic/ folder)
COPY . .

# Copy entrypoint
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Run migrations, then start app
CMD ["./entrypoint.sh"]