import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base

project_root = Path(__file__).resolve().parents[3]
load_dotenv(project_root / ".env")

database_url = os.getenv("DATABASE_URL")
if database_url:
    connection_options = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connection_options)
else:
    database_path = Path(__file__).resolve().parents[2] / "database" / "chatbot.db"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        URL.create("sqlite", database=str(database_path)),
        connect_args={"check_same_thread": False},
    )

session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

base = declarative_base()

def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()