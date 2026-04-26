# app/database.py
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    # Optional for local development; production should set real env vars.
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # If python-dotenv isn't installed or .env is missing, we fall back to OS env vars.
    pass

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()