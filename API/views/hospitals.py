from fastapi import APIRouter, Depends, Query , Request , HTTPException
from sqlalchemy.orm import Session
from API.model import Hospital
from API.database import get_session
from API.schema import HospitalLocationResponse
from cachetools import TTLCache
import httpx
import asyncio
import os
import logging
from slowapi import Limiter 
from slowapi.util import get_remote_address
from dotenv import load_dotenv
import anyio
from pprint import pprint
from typing import Callable , Any
load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

cache = TTLCache(maxsize=1024, ttl=600)

MAP_IR_API_KEY = os.getenv("MAP_IR_API_KEY")
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"
)
# Wrap DB access to run in a thread pool
def get_hospitals_sync(session: Session, insurance_name: str, city: str, medical_class: str):

    hospitals = session.query(Hospital).filter_by(
        insurance=insurance_name,
        city=city,
        medical_class=medical_class
    ).limit(30).all()
    return hospitals

@router.get("/hospital-locations", response_model=HospitalLocationResponse)
@limiter.limit("5/minute")

async def hospital_locations(
    request: Request,
    insurance_name: str = Query(...),
    lat: str = Query(...),
    lng: str = Query(...),
    selected_city: str = Query("تهران"),
    selected_class: str = Query("بیمارستان"),
    session: Session = Depends(get_session)
):
    
    province = 'تهران'
    city = selected_city
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
                province = data.get("province")
                city = data.get("city")
        except Exception as e:
            logger.error(f"Location resolution failed: {str(e)}")
            return {
                "locations": [],
                "failed_hospitals": [],
                "searched_hospitals": []
            }
        
    cache_key_db = f"hospitals_{insurance_name}_{selected_class}_{selected_city}"
    if cache_key_db in cache:
        print('hospitals are cached from the db , returning cach')
        logger.info(f"Returning cached response for {cache_key_db}")
        hospitals = cache[cache_key_db]
    
    # Run sync DB call in a separate thread
    else :
        hospitals = await anyio.to_thread.run_sync(get_hospitals_sync, session, insurance_name, city, selected_class)
        if hospitals:
            cache[cache_key_db] = hospitals
    # for hospital in hospitals:
        # print(f"the data that was taken from DB: {hospital.name}")

    if not hospitals:
        return {
            "locations": [],
            "failed_hospitals": [],
            "searched_hospitals": []
        }

    locations = []
    failed_hospitals = []
    searched_hospitals = []
    cache_key = f"hospitals_locations_{insurance_name}_{selected_class}_{selected_city}"
    if cache_key in cache:
        print('hospitals locations are cached ')
        logger.info(f"Returning cached response for {cache_key}")
        return cache[cache_key]
    async def fetch_location(hospital):
        try:
            request_url = f'https://map.ir/search/v2/autocomplete/?text={hospital.name}&%24filter=province eq {province}&lat={lat}&lon={lng}'
            if city != '':
                request_url = f'https://map.ir/search/v2/autocomplete/?text={hospital.name}&%24filter=city eq {city}&lat={lat}&lon={lng}'
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    request_url,
                    headers={"x-api-key": MAP_IR_API_KEY},
                )
                data = response.json()
                # print(f"the map.ir search param: {hospital.name}")
                if "value" in data:
                    for item in data["value"]:
                        if selected_class in item["title"] or item['fclass'] in ['clinic' , 'hospital' , 'medical']:
                            searched_hospitals.append(item['title'])
                            return item
        except Exception as e:
            logger.error(f"map.ir failed for {hospital.name}: {e}")
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
