import json
from API.model import Hospital
from API.database import get_session, Base, engine
from sqlalchemy.orm import Session

def load_hospitals():
    # Create tables if not already created
    Base.metadata.create_all(bind=engine)

    # Load JSON data
    with open("API/hospitals.json", encoding="utf-8") as f:
        data = json.load(f)

    # Insert into database
    for session in get_session():
        for item in data:
            fields = item["fields"]
            hospital = Hospital(**fields)
            session.add(hospital)
        session.commit()

if __name__ == "__main__":
    load_hospitals()
