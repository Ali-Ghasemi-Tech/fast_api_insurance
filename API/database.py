from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

database_url = "postgresql://root:ANbnYn3tRyS4DgOm2nLsZpmF@insurance:5432/postgres"

engine = create_engine(database_url, echo=True)
print(engine)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
