"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL from environment or auto-detect based on setup
# Priority: 1. Environment variable, 2. Docker setup, 3. Local development
def get_database_url():
    """Get database URL with smart defaults for different environments."""
    # If explicitly set, use that
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    
    # Check if running in Docker (common environment variables)
    in_docker = (
        os.path.exists('/.dockerenv') or 
        os.getenv('DOCKER_CONTAINER') or
        os.path.exists('/app')  # Common Docker workdir
    )
    
    if in_docker:
        # Docker setup: use service name 'postgres'
        return "postgresql://openthreat:openthreat@postgres:5432/openthreat"
    else:
        # Local development: use localhost
        return "postgresql://openthreat:openthreat@localhost:5432/openthreat"

DATABASE_URL = get_database_url()

# For SQLite fallback (development only)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Only use this for development. In production, use Alembic migrations.
    """
    Base.metadata.create_all(bind=engine)
