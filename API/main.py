from fastapi import FastAPI
from API.views.hospitals import router as hospital_router

app = FastAPI(title="Hospital Location API")

# Register the router
app.include_router(hospital_router)
