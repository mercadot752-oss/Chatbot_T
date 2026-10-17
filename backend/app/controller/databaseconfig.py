import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

project_root = Path(__file__).resolve().parents[3]
load_dotenv(project_root / ".env")

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "DATABASE_URL no está configurada. Inicia el proyecto con Docker Compose "
        "para usar PostgreSQL como base de datos única."
    )

engine = create_engine(database_url)

session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()
