"""
Quick Test Script for ClimateGuardAI Setup Verification
CORRECTED VERSION: Works with Gemini/Claude providers
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

import os
from datetime import datetime, timedelta

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

print("=" * 70)
print("🌍 ClimateGuardAI Setup Verification")
print("=" * 70)
print()

# Test 1: Environment Variables
print("Test 1: Checking Environment Variables...")
try:
    from configs.config import settings
    
    # Check LLM provider
    llm_provider = settings.llm_provider
    print_info(f"LLM Provider: {llm_provider}")
    
    # Check based on provider
    if llm_provider == "gemini":
        if settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here":
            print_success("Gemini API key configured")
        else:
            print_error("Gemini API key missing! Set GEMINI_API_KEY in .env")
    
    elif llm_provider == "claude":
        if settings.anthropic_api_key and settings.anthropic_api_key != "your_claude_api_key_here":
            print_success("Anthropic API key configured")
        else:
            print_error("Anthropic API key missing! Set ANTHROPIC_API_KEY in .env")
    
    if settings.openweather_api_key and settings.openweather_api_key != "your_openweather_key_here":
        print_success("OpenWeather API key configured")
    else:
        print_error("OpenWeather API key missing! Set OPENWEATHER_API_KEY in .env")
    
    if settings.gee_project_id:
        print_success(f"Google Earth Engine project configured: {settings.gee_project_id}")
    else:
        print_warning("Google Earth Engine not configured (optional)")
    
    print()
    
except Exception as e:
    print_error(f"Configuration error: {e}")
    print()

# Test 2: Python Dependencies
print("Test 2: Checking Python Dependencies...")
required_packages = [
    ('fastapi', 'FastAPI'),
    ('streamlit', 'Streamlit'),
    ('pandas', 'Pandas'),
    ('torch', 'PyTorch'),
    ('langchain', 'LangChain'),
    ('chromadb', 'ChromaDB'),
    ('plotly', 'Plotly'),
]

missing_packages = []
for package, name in required_packages:
    try:
        __import__(package)
        print_success(f"{name} installed")
    except ImportError:
        print_error(f"{name} not installed")
        missing_packages.append(package)

# Check for LLM packages
if llm_provider == "gemini":
    try:
        from google import genai
        print_success("Google GenAI SDK installed")
    except ImportError:
        print_error("Google GenAI SDK not installed")
        missing_packages.append("google-genai")
elif llm_provider == "claude":
    try:
        import anthropic
        print_success("Anthropic SDK installed")
    except ImportError:
        print_error("Anthropic SDK not installed")
        missing_packages.append("anthropic")

if missing_packages:
    print()
    print_warning(f"Missing packages: {', '.join(missing_packages)}")
    print_info("Run: pip install " + " ".join(missing_packages))

print()

# Test 3: Weather API
print("Test 3: Testing Weather API Connection...")
try:
    from src.data_ingestion.weather_fetcher import WeatherDataFetcher
    from configs.config import settings
    
    weather = WeatherDataFetcher(api_key=settings.openweather_api_key)
    
    # Test with Mumbai coordinates
    data = weather.get_current_weather(19.0760, 72.8777)
    
    if data:
        temp = data['temperature']['current']
        humidity = data['humidity']
        print_success(f"Weather API working! Mumbai: {temp}°C, Humidity: {humidity}%")
    else:
        print_error("Weather API returned no data")
    
except Exception as e:
    print_error(f"Weather API test failed: {e}")

print()

# Test 4: LLM API (Gemini or Claude)
print(f"Test 4: Testing {llm_provider.capitalize()} API Connection...")
try:
    from src.genai.climate_advisor import ClimateAdvisor
    from configs.config import settings
    
    # Initialize based on provider
    if llm_provider == "gemini":
        if not settings.gemini_api_key:
            print_error("Gemini API key not configured!")
        else:
            advisor = ClimateAdvisor(
                api_key=settings.gemini_api_key,
                provider="gemini",
                chroma_persist_dir=settings.chroma_persist_dir
            )
            print_success("Gemini API initialized successfully!")
    
    elif llm_provider == "claude":
        if not settings.anthropic_api_key:
            print_error("Claude API key not configured!")
        else:
            advisor = ClimateAdvisor(
                api_key=settings.anthropic_api_key,
                provider="claude",
                chroma_persist_dir=settings.chroma_persist_dir
            )
            print_success("Claude API initialized successfully!")
    
    # Test a simple generation
    print_info("Testing simple advisory generation...")
    
    test_location = {"name": "Test Location", "lat": 19.0, "lon": 72.0}
    test_forecast = {
        "median": [32, 33, 34, 33, 32, 31, 30],
        "lower_bound": [28, 29, 30, 29, 28, 27, 26],
        "upper_bound": [36, 37, 38, 37, 36, 35, 34]
    }
    test_satellite = {
        "ndvi": {"mean": 0.45},
        "ndwi": {"mean": 0.22}
    }
    
    advisory = advisor.generate_climate_advisory(
        location=test_location,
        weather_forecast=test_forecast,
        satellite_data=test_satellite
    )
    
    if advisory and 'full_text' in advisory:
        print_success("Advisory generation working!")
        print_info(f"Generated advisory length: {len(advisory['full_text'])} characters")
    else:
        print_warning("Advisory generated but format may be incorrect")
    
except Exception as e:
    print_error(f"{llm_provider.capitalize()} API test failed: {e}")

print()

# Test 5: Earth Engine (Optional)
print("Test 5: Testing Google Earth Engine (Optional)...")
try:
    from src.data_ingestion.earth_engine import EarthEngineClient
    from configs.config import settings
    
    ee_client = EarthEngineClient(project_id=settings.gee_project_id)
    print_success("Earth Engine initialized successfully!")
    
    # Test data fetch
    print_info("Testing satellite data fetch...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    sat_data = ee_client.get_sentinel2_data(
        latitude=19.0760,
        longitude=72.8777,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    if sat_data:
        ndvi = sat_data.get('ndvi', {}).get('mean', 'N/A')
        print_success(f"Satellite data working! NDVI: {ndvi}")
    else:
        print_warning("No satellite data available for test location")
    
except Exception as e:
    print_warning(f"Earth Engine not configured or failed: {e}")
    print_info("This is optional - system will work without satellite data")

print()

# Test 6: Directory Structure
print("Test 6: Checking Directory Structure...")
required_dirs = [
    'data',
    'data/raw',
    'data/processed',
    'data/external',
    'models',
    'logs'
]

for dir_path in required_dirs:
    full_path = Path(dir_path)
    if full_path.exists():
        print_success(f"Directory exists: {dir_path}")
    else:
        print_warning(f"Creating directory: {dir_path}")
        full_path.mkdir(parents=True, exist_ok=True)

print()

# Summary
print("=" * 70)
print("📊 Test Summary")
print("=" * 70)
print()

print_info("Configuration:")
print(f"  - LLM Provider: {llm_provider}")
print(f"  - Using {'Gemini (FREE!)' if llm_provider == 'gemini' else 'Claude'}")
print()

print_info("Next Steps:")
print("1. If all tests passed:")
print("   - Start backend: cd src/api && python main.py")
print("   - Start frontend: cd src/ui && streamlit run app.py")
print()
print("2. If some tests failed:")
print("   - Check .env file for API keys")
print("   - Install missing dependencies: pip install -r requirements.txt")
print("   - Review COMPLETE_FIX_GUIDE.md for detailed instructions")
print()
print("3. For Earth Engine setup (optional):")
print("   - Visit: https://earthengine.google.com/")
print("   - Run: earthengine authenticate")
print("   - Can skip for hackathon - set include_satellite=False in UI")
print()

print("=" * 70)
print("Happy hacking! 🚀")
print("=" * 70)