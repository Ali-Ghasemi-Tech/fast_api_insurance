import json
import asyncio
from API.model import Hospital
from API.database import get_async_session, Base, engine
from sqlalchemy.ext.asyncio import AsyncSession

async def load_hospitals():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async for session in get_async_session():
        with open("hospitals.json", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                hospital = Hospital(**item)
                session.add(hospital)
            await session.commit()

if __name__ == "__main__":
    asyncio.run(load_hospitals())
