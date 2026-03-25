# ClimateGuardAI - Complete Setup Guide

## 🚀 Quick Start (15 minutes)

### Prerequisites
- Python 3.10 or higher
- Git
- 16GB RAM (recommended)
- Internet connection

### Step 1: Clone and Setup Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd ClimateGuardAI

# Create virtual environment
conda create -n climateguard python=3.10
conda activate climateguard

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Get API Keys

#### Required APIs:

1. **Anthropic Claude API** (Essential for GenAI)
   - Go to: https://console.anthropic.com/
   - Sign up and get API key
   - Free tier available

2. **OpenWeatherMap API** (Essential for weather data)
   - Go to: https://openweathermap.org/api
   - Sign up for free tier
   - Get API key from dashboard

3. **Google Earth Engine** (Optional but recommended)
   - Go to: https://earthengine.google.com/
   - Sign up with Google account
   - Request access (usually approved in 24-48 hours)
   - Create project and download credentials JSON

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys
nano .env  # or use any text editor
```

**Minimum required in .env:**
```
ANTHROPIC_API_KEY=your_claude_api_key_here
OPENWEATHER_API_KEY=your_openweather_key_here
```

**Optional (for full features):**
```
GOOGLE_APPLICATION_CREDENTIALS=path/to/gee-credentials.json
GEE_PROJECT_ID=your_gee_project_id
```

### Step 4: Setup Google Earth Engine (Optional)

If you want satellite data:

```bash
# Install Earth Engine CLI
pip install earthengine-api

# Authenticate (follow prompts)
earthengine authenticate

# Initialize
python -c "import ee; ee.Initialize()"
```

### Step 5: Download Climate Knowledge Base

For RAG (Retrieval Augmented Generation):

```bash
# Create directory for climate documents
mkdir -p data/external/climate_docs

# Download sample documents
# Option 1: IPCC Reports (recommended)
wget https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_SPM.pdf -P data/external/climate_docs/

# Option 2: India-specific reports
# Download from: https://moef.gov.in/en/climate-change/
```

**Index the documents:**
```python
from src.genai.climate_advisor import ClimateAdvisor
from configs.config import settings

advisor = ClimateAdvisor(
    anthropic_api_key=settings.anthropic_api_key,
    chroma_persist_dir=settings.chroma_persist_dir
)

# Index documents
advisor.index_climate_documents('data/external/climate_docs')
```

### Step 6: Run the Application

**Terminal 1 - Start Backend API:**
```bash
cd ClimateGuardAI
conda activate climateguard

# Run FastAPI server
cd src/api
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Frontend UI:**
```bash
cd ClimateGuardAI
conda activate climateguard

# Run Streamlit
cd src/ui
streamlit run app.py
```

**Access the application:**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🧪 Testing the Setup

### Quick Test Script

Create `test_setup.py`:

```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from configs.config import settings
from src.data_ingestion.weather_fetcher import WeatherDataFetcher
from src.genai.climate_advisor import ClimateAdvisor

print("Testing ClimateGuardAI Setup...")

# Test 1: Weather API
print("\n1. Testing Weather API...")
try:
    weather = WeatherDataFetcher(api_key=settings.openweather_api_key)
    data = weather.get_current_weather(19.0760, 72.8777)
    print(f"✅ Weather API working! Current temp in Mumbai: {data['temperature']['current']}°C")
except Exception as e:
    print(f"❌ Weather API failed: {e}")

# Test 2: Claude API
print("\n2. Testing Claude API...")
try:
    advisor = ClimateAdvisor(anthropic_api_key=settings.anthropic_api_key)
    print("✅ Claude API initialized successfully!")
except Exception as e:
    print(f"❌ Claude API failed: {e}")

# Test 3: Earth Engine (optional)
print("\n3. Testing Google Earth Engine...")
try:
    from src.data_ingestion.earth_engine import EarthEngineClient
    ee_client = EarthEngineClient(project_id=settings.gee_project_id)
    print("✅ Earth Engine working!")
except Exception as e:
    print(f"⚠️  Earth Engine not configured (optional): {e}")

print("\n✅ Setup complete! Ready to use ClimateGuardAI")
```

Run test:
```bash
python test_setup.py
```

## 🐛 Troubleshooting

### Issue: "Module not found" errors
**Solution:**
```bash
# Make sure you're in the right environment
conda activate climateguard

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### Issue: "Earth Engine authentication failed"
**Solution:**
```bash
# Re-authenticate
earthengine authenticate

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

### Issue: "API rate limit exceeded"
**Solution:**
- OpenWeatherMap free tier: 60 calls/minute
- Use caching in production
- Upgrade to paid tier if needed

### Issue: "ChromaDB persistence error"
**Solution:**
```bash
# Clear and recreate
rm -rf data/chroma_db
python -c "from src.genai.climate_advisor import ClimateAdvisor; ClimateAdvisor('your-key')"
```

## 📦 Minimal Setup (No Satellite Data)

If you can't get Google Earth Engine access:

1. Set `include_satellite=False` in API calls
2. System will work with weather data only
3. Advisory will still be generated but without satellite indices

**Modify .env:**
```
# Comment out or remove
# GOOGLE_APPLICATION_CREDENTIALS=...
# GEE_PROJECT_ID=...
```

## 🎯 For Hackathon Demo

### Recommended Test Locations:

1. **Mumbai, Maharashtra**: `19.0760, 72.8777`
2. **Nashik, Maharashtra**: `19.9975, 73.7898` (agricultural region)
3. **Delhi**: `28.6139, 77.2090` (urban heat island)
4. **Bengaluru**: `12.9716, 77.5946` (moderate climate)

### Demo Flow:

1. Open Streamlit UI
2. Select "Nashik, Maharashtra"
3. Generate advisory
4. Show:
   - Weather forecast graphs
   - Satellite vegetation indices
   - AI-generated crop recommendations
   - Risk assessment
   - Voice advisory

### Creating Presentation Slides:

Your demo should highlight:
1. **Problem**: Lack of hyperlocal climate intelligence
2. **Solution**: Multi-modal AI combining satellite + weather + LLM
3. **Tech**: TFT forecasting + Claude RAG + Real-time APIs
4. **Impact**: Helps farmers prevent crop loss
5. **Live Demo**: Show working prototype

## 🚀 Advanced Features (After Basic Setup)

### 1. Add Historical Data
```python
# Download and process historical weather
from src.data_ingestion.weather_fetcher import WeatherDataFetcher
# Implement batch historical data collection
```

### 2. Train Custom Models
```python
# Train TFT model on collected data
from src.modeling.weather_forecasting import WeatherForecaster
# Follow training examples in the module
```

### 3. Add WhatsApp Bot
```bash
# Install Twilio
pip install twilio

# Configure in .env
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
```

### 4. Deploy to Cloud
```bash
# Docker build
docker build -t climateguard .

# Deploy to AWS/GCP/Azure
# See deployment docs
```

## 📞 Support

If you encounter issues:
1. Check logs in `logs/` directory
2. Verify all API keys in `.env`
3. Test individual modules
4. Check GitHub issues

## ✅ Checklist Before Demo

- [ ] All API keys configured
- [ ] Backend running on :8000
- [ ] Frontend running on :8501
- [ ] Test with at least 2 locations
- [ ] Download PDF report working
- [ ] Screenshots/recordings ready
- [ ] Presentation deck prepared
- [ ] GitHub repository public/private as required

Good luck with your hackathon! 🚀