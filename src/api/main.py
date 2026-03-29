"""
FastAPI Backend for ClimateGuardAI
CORRECTED VERSION: Runs uvicorn server correctly
"""

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env from project root
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)
print(f"✅ Loading .env from: {env_path}")

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import sys

# Add project root to path
sys.path.append(str(project_root))

from configs.config import settings
from src.data_ingestion.weather_fetcher import WeatherDataFetcher
from src.genai.climate_advisor import ClimateAdvisor
from loguru import logger

# Try importing Earth Engine
try:
    from src.data_ingestion.earth_engine import EarthEngineClient
    earth_engine = EarthEngineClient(project_id=settings.gee_project_id) if settings.gee_project_id else None
except Exception as e:
    logger.warning(f"Google Earth Engine not initialized: {e}")
    earth_engine = None

# Initialize FastAPI app
app = FastAPI(
    title="ClimateGuardAI API",
    description="Hyperlocal Climate Risk & Adaptation Advisory",
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

# Initialize clients
weather_fetcher = WeatherDataFetcher(api_key=settings.openweather_api_key)

# Initialize ClimateAdvisor based on provider
if settings.llm_provider == "gemini":
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY not set in .env file!")
    
    climate_advisor = ClimateAdvisor(
        api_key=settings.gemini_api_key,
        provider="gemini",
        chroma_persist_dir=settings.chroma_persist_dir
    )
    logger.info("Using Gemini as LLM provider")
    
elif settings.llm_provider == "claude":
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in .env file!")
    
    climate_advisor = ClimateAdvisor(
        api_key=settings.anthropic_api_key,
        provider="claude",
        chroma_persist_dir=settings.chroma_persist_dir
    )
    logger.info("Using Claude as LLM provider")
    
else:
    raise ValueError(f"Invalid LLM_PROVIDER: {settings.llm_provider}")


# Pydantic models
class LocationRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    name: Optional[str] = None


class ClimateAdvisoryRequest(BaseModel):
    latitude: float
    longitude: float
    location_name: Optional[str] = None
    forecast_days: int = Field(7, ge=1, le=14)
    include_satellite: bool = True
    language: str = "en"


class AdvisoryResponse(BaseModel):
    location: Dict
    timestamp: datetime
    weather_forecast: Dict
    satellite_data: Optional[Dict] = None
    advisory: Dict
    risk_level: str


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "ClimateGuardAI API",
        "version": "1.0.0",
        "llm_provider": settings.llm_provider
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "weather_api": "online",
            "earth_engine": "online" if earth_engine else "offline",
            "genai": "online",
            "llm_provider": settings.llm_provider
        }
    }


@app.post("/weather/current")
async def get_current_weather(location: LocationRequest):
    """Get current weather for a location"""
    try:
        weather_data = weather_fetcher.get_current_weather(
            location.latitude,
            location.longitude
        )
        
        if not weather_data:
            raise HTTPException(status_code=404, detail="Weather data not available")
        
        return weather_data
        
    except Exception as e:
        logger.error(f"Error fetching current weather: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/weather/forecast")
async def get_weather_forecast(
    location: LocationRequest,
    days: int = 7
):
    """Get weather forecast"""
    try:
        forecast_df = weather_fetcher.get_forecast(
            location.latitude,
            location.longitude,
            days=days
        )
        
        if forecast_df.empty:
            raise HTTPException(status_code=404, detail="Forecast not available")
        
        # Aggregate to daily
        daily_forecast = weather_fetcher.aggregate_daily_forecast(forecast_df)
        
        return {
            "location": {
                "lat": location.latitude,
                "lon": location.longitude,
                "name": location.name
            },
            "forecast": daily_forecast.to_dict(orient='records')
        }
        
    except Exception as e:
        logger.error(f"Error fetching forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/satellite/vegetation")
async def get_vegetation_indices(
    location: LocationRequest,
    days_back: int = 30
):
    """Get satellite vegetation indices (NDVI, NDWI, EVI)"""
    if not earth_engine:
        raise HTTPException(
            status_code=503,
            detail="Earth Engine service not available"
        )
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        satellite_data = earth_engine.get_sentinel2_data(
            latitude=location.latitude,
            longitude=location.longitude,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not satellite_data:
            raise HTTPException(
                status_code=404,
                detail="Satellite data not available"
            )
        
        return satellite_data
        
    except Exception as e:
        logger.error(f"Error fetching satellite data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/advisory/generate")
async def generate_advisory(request: ClimateAdvisoryRequest):
    """Generate comprehensive climate advisory"""
    try:
        logger.info(f"Generating advisory for {request.latitude}, {request.longitude}")
        
        # 1. Get weather forecast
        forecast_df = weather_fetcher.get_forecast(
            request.latitude,
            request.longitude,
            days=request.forecast_days
        )
        
        if forecast_df.empty:
            raise HTTPException(status_code=404, detail="Forecast not available")
        
        daily_forecast = weather_fetcher.aggregate_daily_forecast(forecast_df)
        
        # Create forecast dict for GenAI
        weather_forecast = {
            "median": daily_forecast['temperature'].tolist(),
            "lower_bound": daily_forecast['temp_min'].tolist(),
            "upper_bound": daily_forecast['temp_max'].tolist(),
            "humidity": daily_forecast['humidity'].tolist(),
            "rainfall": daily_forecast['total_rainfall'].tolist()
        }
        
        # 2. Get satellite data (if requested)
        satellite_data = {}
        if request.include_satellite and earth_engine:
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                
                sat_data = earth_engine.get_sentinel2_data(
                    latitude=request.latitude,
                    longitude=request.longitude,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )
                
                if sat_data:
                    satellite_data = sat_data
                    
                # Get temperature data
                temp_data = earth_engine.get_landsat_temperature(
                    latitude=request.latitude,
                    longitude=request.longitude,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )
                
                if temp_data:
                    satellite_data['temperature_celsius'] = temp_data['temperature_celsius']
                    
            except Exception as e:
                logger.warning(f"Satellite data fetch failed: {e}")
        
        # 3. Build location dict
        location = {
            "name": request.location_name or f"{request.latitude}, {request.longitude}",
            "lat": request.latitude,
            "lon": request.longitude
        }
        
        # 4. Generate AI advisory
        logger.info("Calling ClimateAdvisor to generate advisory...")
        advisory = climate_advisor.generate_climate_advisory(
            location=location,
            weather_forecast=weather_forecast,
            satellite_data=satellite_data,
            historical_events=[]
        )
        
        # 5. Determine risk level
        risk_level = determine_risk_level(weather_forecast, satellite_data)
        
        response = {
            "location": location,
            "timestamp": datetime.now().isoformat(),
            "weather_forecast": weather_forecast,
            "satellite_data": satellite_data if satellite_data else None,
            "advisory": advisory,
            "risk_level": risk_level
        }
        
        logger.info(f"Advisory generated successfully for {location['name']}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating advisory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/advisory/voice")
async def get_voice_advisory(request: ClimateAdvisoryRequest):
    """Get voice-friendly advisory"""
    try:
        # First generate full advisory
        advisory_response = await generate_advisory(request)
        
        # Convert to voice format
        voice_text = climate_advisor.generate_voice_advisory(
            advisory=advisory_response['advisory'],
            language=request.language
        )
        
        return {
            "location": advisory_response['location'],
            "risk_level": advisory_response['risk_level'],
            "voice_message": voice_text,
            "language": request.language
        }
        
    except Exception as e:
        logger.error(f"Error generating voice advisory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/crops/recommendations")
async def get_crop_recommendations(
    latitude: float,
    longitude: float,
    season: str = "kharif"
):
    """Get crop recommendations based on location and season"""
    try:
        from configs.config import CROP_DATABASE
        
        recommended_crops = CROP_DATABASE.get(season.lower(), [])
        
        return {
            "location": {"lat": latitude, "lon": longitude},
            "season": season,
            "recommended_crops": recommended_crops,
            "note": "Recommendations based on general patterns."
        }
        
    except Exception as e:
        logger.error(f"Error getting crop recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def determine_risk_level(
    weather_forecast: Dict,
    satellite_data: Dict
) -> str:
    """Determine overall climate risk level"""
    risk_score = 0
    
    if weather_forecast.get('median'):
        avg_temp = sum(weather_forecast['median']) / len(weather_forecast['median'])
        if avg_temp > 40:
            risk_score += 3
        elif avg_temp > 35:
            risk_score += 2
        elif avg_temp < 10:
            risk_score += 2
    
    if weather_forecast.get('rainfall'):
        total_rainfall = sum(weather_forecast['rainfall'])
        if total_rainfall < 10:
            risk_score += 2
        elif total_rainfall > 200:
            risk_score += 3
    
    if satellite_data and 'ndvi' in satellite_data:
        ndvi = satellite_data['ndvi'].get('mean', 0.5)
        if ndvi < 0.2:
            risk_score += 2
    
    if risk_score >= 5:
        return "HIGH"
    elif risk_score >= 3:
        return "MEDIUM"
    else:
        return "LOW"


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("🌍 ClimateGuardAI Backend Server")
    print("="*70)
    print(f"🚀 Starting server on http://0.0.0.0:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"🔧 Provider: {settings.llm_provider.upper()}")
    print("="*70 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to False to avoid the warning
        log_level="info"
    )