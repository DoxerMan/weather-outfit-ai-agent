from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from app.services.weather_service import WeatherService
from app.services.outfit_agent import OutfitAgent
from app.database import init_db

load_dotenv()

app = FastAPI(
    title="Weather Outfit AI Agent",
    description="AI-powered outfit recommendations based on weather conditions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
weather_service = WeatherService(os.getenv("OPENWEATHER_API_KEY"))
outfit_agent = OutfitAgent(os.getenv("OPENAI_API_KEY"))


@app.on_event("startup")
async def startup():
    init_db()


class OutfitRequest(BaseModel):
    location: str
    occasion: Optional[str] = "casual"
    user_id: Optional[str] = None


class ClothingItem(BaseModel):
    name: str
    type: str  # top, bottom, shoes, outerwear, accessory
    warmth_level: str  # cold, cool, mild, warm, hot
    waterproof: bool = False
    colors: List[str] = []
    formality: str = "casual"  # casual, business, formal


@app.get("/")
async def root():
    return {
        "message": "Weather Outfit AI Agent API",
        "version": "1.0.0",
        "endpoints": [
            "/weather/{location}",
            "/recommend",
            "/wardrobe"
        ]
    }


@app.get("/weather/{location}")
async def get_weather(location: str):
    """Get current weather for a location"""
    try:
        weather_data = await weather_service.get_weather(location)
        return weather_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend")
async def recommend_outfit(request: OutfitRequest):
    """Get outfit recommendation based on weather and preferences"""
    try:
        # Get weather data
        weather_data = await weather_service.get_weather(request.location)
        
        # Generate outfit recommendation
        recommendation = await outfit_agent.recommend_outfit(
            weather_data=weather_data,
            occasion=request.occasion,
            user_id=request.user_id
        )
        
        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/wardrobe/items")
async def add_clothing_item(item: ClothingItem):
    """Add a clothing item to wardrobe"""
    # This would interact with database in full implementation
    return {"message": "Item added", "item": item}


@app.get("/wardrobe/items")
async def list_wardrobe():
    """List all clothing items in wardrobe"""
    # This would fetch from database
    return {"items": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )