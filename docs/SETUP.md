# ClimateGuardAI - Setup Guide

Complete installation and configuration guide for ClimateGuardAI.

---

## 📋 Prerequisites

- **Python:** 3.10 or higher
- **RAM:** 4GB minimum (8GB recommended)
- **Storage:** 2GB free space
- **Internet:** Required for API calls

---

## 🚀 Quick Start (5 Minutes)

### 1. Clone Repository

```bash
git clone https://github.com/akshat-lakum/ClimateGuardAI.git
cd ClimateGuardAI
```

### 2. Run Setup Script

```bash
python quick_setup.py
```

This will:
- Create all necessary directories
- Set up `.env` template
- Check dependencies

### 3. Configure API Keys

```bash
# Copy template
copy .env.example .env

# Edit with your keys
notepad .env
```

Add your API keys:
```env
GEMINI_API_KEY=your_gemini_key_here
OPENWEATHER_API_KEY=your_openweather_key_here
GEE_PROJECT_ID=your_gee_project_id_here
LLM_PROVIDER=gemini
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Test Setup

```bash
python test_setup.py
```

All tests should pass with ✅ checkmarks!

### 6. Run Application

**Terminal 1 - Backend:**
```bash
python src/api/main.py
```

**Terminal 2 - Frontend:**
```bash
streamlit run src/ui/app.py
```

**Open browser:** http://localhost:8501

---

## 🔑 Getting API Keys

### Google Gemini (FREE - 1.5M requests/month)

1. Visit: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key starting with `AIza...`
4. Paste in `.env` as `GEMINI_API_KEY`

### OpenWeatherMap (FREE - 1M calls/day)

1. Visit: https://openweathermap.org/api
2. Sign up for free account
3. Go to "API keys" tab
4. Copy your key
5. Paste in `.env` as `OPENWEATHER_API_KEY`

### Google Earth Engine (OPTIONAL - FREE)

1. Visit: https://earthengine.google.com/
2. Sign up with Google account
3. Create a project
4. Note your project ID
5. Paste in `.env` as `GEE_PROJECT_ID`

**Note:** Earth Engine is optional. System works without it!

---

## 🐍 Detailed Python Setup

### Option 1: Using Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Mac/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Option 2: Using Conda

```bash
conda create -n climateguard python=3.10
conda activate climateguard
pip install -r requirements.txt
```

### Verify Installation

```bash
python -c "import fastapi, streamlit, torch, google.genai; print('✅ All packages installed!')"
```

---

## 📁 Directory Structure

After setup, your structure should look like:

```
ClimateGuardAI/
├── .venv/                  # Virtual environment (local only)
├── configs/                # Configuration files
│   └── config.py
├── data/                   # Data storage
│   ├── raw/               # Raw data cache
│   ├── processed/         # Processed datasets
│   ├── external/          # External data (IMD, IPCC)
│   └── chroma_db/         # Vector database
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   ├── IMPACT_MODEL.md
│   └── SETUP.md (this file)
├── models/                 # ML models
│   ├── forecasting/
│   ├── risk_assessment/
│   └── crop_recommendation/
├── src/                    # Source code
│   ├── api/               # FastAPI backend
│   ├── data_ingestion/    # Data collection agents
│   ├── genai/             # GenAI synthesis
│   ├── modeling/          # ML models
│   └── ui/                # Streamlit frontend
├── logs/                   # Application logs
├── .env                    # Environment variables (local only!)
├── .env.example            # Template for .env
├── .gitignore             # Git ignore rules
├── quick_setup.py         # Setup script
├── requirements.txt       # Python dependencies
├── test_setup.py          # Setup verification
└── README.md              # Main documentation
```

---

## 🧪 Testing

### Run All Tests

```bash
# Full test suite
pytest tests/

# Specific tests
python test_gemini.py      # Test Gemini API
python test_weather.py     # Test Weather API
python test_setup.py       # Test complete setup
```

### Expected Test Output

```
✅ Gemini API key configured
✅ OpenWeather API key configured
✅ All packages installed
✅ Weather API working! Mumbai: 30.98°C
✅ Gemini API initialized successfully!
✅ Advisory generation working!
```

---

## 🐛 Troubleshooting

### Issue: Import Errors

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: API Key Errors

**Error:** `GEMINI_API_KEY not set`

**Solution:**
1. Create `.env` file: `copy .env.example .env`
2. Add your actual API keys
3. Restart the application

### Issue: Port Already in Use

**Error:** `Port 8000 already in use`

**Windows Solution:**
```cmd
netstat -ano | findstr :8000
taskkill /PID [PID_NUMBER] /F
```

**Mac/Linux Solution:**
```bash
lsof -ti:8000 | xargs kill -9
```

### Issue: ChromaDB Errors

**Error:** `chromadb.errors.InvalidDimensionException`

**Solution:**
```bash
# Delete and recreate vector database
rm -rf data/chroma_db
python quick_setup.py
```

### Issue: Satellite Data Not Loading

**Error:** `Earth Engine not initialized`

**Solutions:**
1. Add `GEE_PROJECT_ID` to `.env`
2. OR uncheck "Include Satellite Data" in UI
3. System works fine without satellite data!

---

## ⚙️ Configuration

### Environment Variables

**Required:**
- `GEMINI_API_KEY` - Your Gemini API key
- `OPENWEATHER_API_KEY` - Your OpenWeather API key
- `LLM_PROVIDER` - Set to `gemini`

**Optional:**
- `GEE_PROJECT_ID` - Google Earth Engine project ID
- `DEBUG` - Enable debug logging (default: True)
- `LOG_LEVEL` - Logging level (default: INFO)
- `CHROMA_PERSIST_DIR` - Vector DB location (default: data/chroma_db)

### Customization

Edit `configs/config.py` to customize:
- Forecast days (default: 7)
- Grid size (default: 5km)
- Model paths
- RAG settings (chunk size, overlap)

---

## 🚀 Deployment

### Local Development

Already covered above! Use:
```bash
python src/api/main.py
streamlit run src/ui/app.py
```

### Production Deployment (Future)

**Option 1: Docker** (Coming soon)
```bash
docker-compose up
```

**Option 2: Cloud Deployment**
- AWS EC2 / GCP Compute Engine
- Deploy FastAPI with Gunicorn + Nginx
- Deploy Streamlit separately or use FastAPI to serve

**Option 3: Streamlit Cloud**
```bash
# Deploy frontend to Streamlit Cloud
# Connect to your backend API
```

---

## 📊 Performance Optimization

### Caching

System uses multiple caching layers:
1. **Redis** - API response caching
2. **ChromaDB** - RAG knowledge caching
3. **Local storage** - Weather/satellite data caching

### Reducing API Costs

1. **Enable caching** in `configs/config.py`
2. **Increase cache TTL** for stable data
3. **Batch requests** when possible
4. **Use offline mode** for demos

---

## 🔒 Security

### API Key Protection

- ✅ `.env` is in `.gitignore` (never committed)
- ✅ Use environment variables (not hardcoded)
- ✅ Rotate keys regularly
- ❌ NEVER commit `.env` to GitHub
- ❌ NEVER share API keys publicly

### Data Privacy

- No personally identifiable information (PII) stored
- Only location coordinates collected
- All data anonymized
- GDPR/privacy compliant

---

## 📚 Additional Resources

- **Architecture:** See `docs/ARCHITECTURE.md`
- **Impact Model:** See `docs/IMPACT_MODEL.md`
- **API Docs:** http://localhost:8000/docs (when backend running)
- **GitHub:** https://github.com/akshat-lakum/ClimateGuardAI

---

## 💬 Support

**Having issues?**

1. Check troubleshooting section above
2. Run `python test_setup.py` to diagnose
3. Review error logs in `logs/` folder
4. Open GitHub issue with error details

---

## ✅ Quick Checklist

Before running:
- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with API keys
- [ ] `python test_setup.py` passes
- [ ] Backend starts without errors
- [ ] Frontend opens in browser

---

**You're ready to run ClimateGuardAI!** 🌍🚀

For hackathon submission, see `docs/DEMO_VIDEO_SCRIPT.md` for recording instructions.












