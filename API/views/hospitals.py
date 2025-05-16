from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from API.model import Hospital
from API.database import get_async_session
from API.schema import HospitalLocationResponse
from cachetools import TTLCache
import httpx
import asyncio
import os
import logging
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory cache: max 1024 items, TTL 600 seconds
cache = TTLCache(maxsize=1024, ttl=600)

MAP_IR_API_KEY = os.getenv("MAP_IR_API_KEY")

async def get_hospitals(session: AsyncSession, insurance_name: str, city: str, medical_class: str):
    cache_key = f"hospitals_{insurance_name}_{city}_{medical_class}"
    if cache_key in cache:
        logger.info(f"Cache HIT for {cache_key}")
        return cache[cache_key]

    logger.info(f"Cache MISS for {cache_key}")
    result = await session.execute(
        select(Hospital).where(
            Hospital.insurance == insurance_name,
            Hospital.city == city,
            Hospital.medical_class == medical_class
        )
    )
    hospitals = result.scalars().all()
    cache[cache_key] = hospitals
    return hospitals


@router.get("/hospital-locations", response_model=HospitalLocationResponse)
async def hospital_locations(
    insurance_name: str = Query(...),
    lat: str = Query(...),
    lng: str = Query(...),
    selected_city: str = Query("تهران"),
    selected_class: str = Query("بیمارستان"),
    session: AsyncSession = Depends(get_async_session)
):
    cache_key = f"hospitals_{insurance_name}_{lat}_{lng}_{selected_class}"
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

    hospitals = await get_hospitals(session, insurance_name, city, selected_class)
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
            request_url = f'https://map.ir/search/v2/autocomplete/?text={hospital.name}&%24filter=city eq {city}&lat={lat}&lon={lng}'
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    request_url,
                    headers={"x-api-key": MAP_IR_API_KEY}
                )
                data = response.json()
                if "value" in data:
                    for item in data["value"]:
                        if selected_class in item["title"]:
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

    cache[cache_key] = response_data
    return response_data
