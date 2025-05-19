import json
from API.model import Hospital
from API.database import SessionLocal, Base, engine
from sqlalchemy import select

def load_hospitals():
    # Create tables if not already created
    Base.metadata.create_all(bind=engine)

    # Load JSON data
    with open("API/hospitals.json", encoding="utf-8") as f:
        data = json.load(f)

    # Use a single DB session
    with SessionLocal() as session:
        for item in data:
            fields = item["fields"]

            # Check for existing record (adjust logic if needed)

            insurance_hospitals = Hospital(**fields)
            session.add(insurance_hospitals)

        session.commit()

if __name__ == "__main__":
    load_hospitals()
