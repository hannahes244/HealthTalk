# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chat import router as chat_router
from config.settings import settings # Import your settings

app = FastAPI(
    title="HealthTalk Medical Assistant API",
    description="Backend for an AI-powered medical assistant.",
    version="0.1.0",
)

# Configure CORS using settings
origins = settings.CORS_ORIGINS # From your config/settings.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")

@app.get("/")
async def read_root():
    return {"message": "Medical Assistant Backend is running!"}

# pip install uvicorn
# uvicorn main:app --reload --port 8001