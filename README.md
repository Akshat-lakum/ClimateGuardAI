# ClimateGuardAI 🌍

Hyperlocal Climate Risk & Adaptation Advisor using GenAI

## Overview
ClimateGuardAI provides village/ward-level climate intelligence for farmers, urban planners, and disaster management authorities. It combines satellite data, weather forecasts, IoT sensors, and GenAI to deliver actionable climate adaptation strategies.

## Features
- 🛰️ Satellite imagery analysis (5km² resolution)
- 🌡️ 7-day hyperlocal weather forecasting
- 🌾 AI-powered crop recommendations
- 🚨 Early disaster warnings
- 💬 Multilingual voice interface
- 📱 WhatsApp bot integration

## Tech Stack
- **ML/AI**: PyTorch, TensorFlow, Transformers
- **GenAI**: Claude API, LangChain, RAG
- **Geospatial**: Google Earth Engine, Rasterio, GeoPandas
- **Time Series**: PyTorch Forecasting, Darts
- **Backend**: FastAPI, PostgreSQL, Redis
- **Frontend**: Streamlit, Gradio
- **Deployment**: Docker, AWS/GCP

## Project Structure
```
ClimateGuardAI/
├── data/                      # Data storage
│   ├── raw/                   # Raw satellite/weather data
│   ├── processed/             # Preprocessed datasets
│   └── external/              # External datasets (IMD, IPCC)
├── models/                    # Trained models
│   ├── forecasting/           # Weather prediction models
│   ├── risk_assessment/       # Risk scoring models
│   └── crop_recommendation/   # Crop advisory models
├── src/                       # Source code
│   ├── data_ingestion/        # Data collection modules
│   ├── preprocessing/         # Data cleaning & feature engineering
│   ├── modeling/              # ML model training
│   ├── genai/                 # LLM integration & RAG
│   ├── api/                   # FastAPI endpoints
│   └── utils/                 # Helper functions
├── notebooks/                 # Jupyter notebooks for EDA
├── tests/                     # Unit tests
├── configs/                   # Configuration files
├── docker/                    # Docker configurations
├── docs/                      # Documentation
└── scripts/                   # Utility scripts

```

## Quick Start

### Prerequisites
- Python 3.10+
- Google Earth Engine account
- Claude API key
- 16GB RAM recommended

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/ClimateGuardAI.git
cd ClimateGuardAI

# Create virtual environment
conda create -n climateguard python=3.10
conda activate climateguard

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your API keys to .env
```

### Run Demo
```bash
# Start backend API
cd src/api
uvicorn main:app --reload

# Start Streamlit UI (in another terminal)
cd src/ui
streamlit run app.py
```

## Data Sources
1. **Satellite**: Google Earth Engine (Sentinel-2, Landsat)
2. **Weather**: IMD, OpenWeatherMap
3. **Agriculture**: AgriStack, Crop Cutting Experiments
4. **Climate Reports**: IPCC AR6, NATCOM reports

## Contributors
- Your Team Name
- ET GenAI Hackathon 2025

## License
MIT License