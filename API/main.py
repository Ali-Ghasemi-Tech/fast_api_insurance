from fastapi import FastAPI
from API.views.hospitals import router as hospital_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Hospital Location API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the router
app.include_router(hospital_router)
