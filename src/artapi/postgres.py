from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from .config import DATABASE_URL


engine = create_engine(
    DATABASE_URL
)
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=True, 
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()
