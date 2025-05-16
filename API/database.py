from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL" , "postgresql://root:ANbnYn3tRyS4DgOm2nLsZpmF@insurance:5432/insurance")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()

async def get_async_session():
    async with SessionLocal() as session:
        yield session
