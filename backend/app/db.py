from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# SQLAlchemy Base class for models to inherit
Base = declarative_base()

# Create SQLAlchemy engine (connects to Postgres)
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # helps avoid stale connections
)

# Factory that creates DB sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency we will use in FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()