from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from API.model import Hospital
from API.database import get_session
from API.schema import HospitalLocationResponse
from cachetools import TTLCache
import httpx
import asyncio
import os
import logging
from dotenv import load_dotenv
import anyio
from pprint import pprint

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

cache = TTLCache(maxsize=1024, ttl=10)

MAP_IR_API_KEY = os.getenv("MAP_IR_API_KEY")

# Wrap DB access to run in a thread pool
def get_hospitals_sync(session: Session, insurance_name: str, city: str, medical_class: str):
    cache_key = f"hospitals_{insurance_name}_{city}_{medical_class}"
    if cache_key in cache:
        logger.info(f"Cache HIT for {cache_key}")
        return cache[cache_key]

    logger.info(f"Cache MISS for {cache_key}")
    hospitals = session.query(Hospital).filter_by(
        insurance=insurance_name,
        city=city,
        medical_class=medical_class
    ).limit(20).all()
    if hospitals:
        cache[cache_key] = hospitals
    return hospitals

@router.get("/hospital-locations", response_model=HospitalLocationResponse)
async def hospital_locations(
    insurance_name: str = Query(...),
    lat: str = Query(...),
    lng: str = Query(...),
    selected_city: str = Query("تهران"),
    selected_class: str = Query("بیمارستان"),
    session: Session = Depends(get_session)
):
    
    cache_key = f"hospitals_{insurance_name}_{selected_class}_{selected_city}"
    if cache_key in cache:
        logger.info(f"Returning cached response for {cache_key}")
        return cache[cache_key]
    city, province = selected_city, selected_city
    if selected_city == "مکان فعلی من":
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://map.ir/reverse/fast-reverse",
                    headers={"x-api-key": MAP_IR_API_KEY},
                    params={"lat": lat, "lon": lng}
                )
                response.raise_for_status()
                data = response.json()
                province = data.get("province", "تهران")
                city = data.get("city", "تهران")
        except Exception as e:
            logger.error(f"Location resolution failed: {str(e)}")
            return {
                "locations": [],
                "failed_hospitals": [],
                "searched_hospitals": []
            }

    # Run sync DB call in a separate thread
    hospitals = await anyio.to_thread.run_sync(get_hospitals_sync, session, insurance_name, city, selected_class)
    print(f"the data that was taken from DB: {hospitals}")

    if not hospitals:
        return {
            "locations": [],
            "failed_hospitals": [],
            "searched_hospitals": []
        }

    locations = []
    failed_hospitals = []
    searched_hospitals = [h.name for h in hospitals]

    async def fetch_location(hospital):
        
        try:
            cache_key = f"hospitals_{insurance_name}_{selected_class}_{selected_city}"
            if cache_key in cache:
                logger.info(f"Returning cached response for {cache_key}")
                return cache[cache_key]
            
            request_url = f'https://map.ir/search/v2/autocomplete/?text={hospital.name}&%24filter=province eq {province}&lat={lat}&lon={lng}'
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    request_url,
                    headers={"x-api-key": MAP_IR_API_KEY},
                )
                data = response.json()
                print(f"the map.ir search param: {hospital.name}")
                if "value" in data:
                    for item in data["value"]:
                        if selected_class in item["title"] or item['fclass'] in ['clinic' , 'hospital' , 'medical']:
                            return item
        except Exception as e:
            logger.error(f"map.ir failed for {hospital.name}: {str(e)}")
            failed_hospitals.append(hospital.name)
        return None

    async def worker(hospital):
        result = await fetch_location(hospital)
        if result:
            locations.append(result)

    await asyncio.gather(*[worker(h) for h in hospitals])

    response_data = {
        "locations": locations,
        "failed_hospitals": failed_hospitals,
        "searched_hospitals": searched_hospitals
    }
    if response_data.get('locations') != []:
        cache[cache_key] = response_data
    return response_data
