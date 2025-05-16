import json
import asyncio
from API.database import SessionLocal  # direct sessionmaker, not the generator
from API.model import Hospital

path = "API/hospitals.json"
async def import_hospitals():
    async with SessionLocal() as session:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

            for entry in data:
                fields = entry["fields"]
                hospital = Hospital(**fields)
                session.add(hospital)

        await session.commit()
    print("✅ Data imported successfully!")

if __name__ == "__main__":
    asyncio.run(import_hospitals())
