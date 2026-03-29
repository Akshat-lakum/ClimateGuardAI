"""
Quick Setup Script for ClimateGuardAI
Restores all necessary files after cloning from GitHub
"""
import os
from pathlib import Path

def create_directories():
    """Create all necessary directories"""
    directories = [
        'data/raw',
        'data/processed',
        'data/external',
        'data/chroma_db',
        'data/offline_cache',
        'models/forecasting',
        'models/risk_assessment',
        'models/crop_recommendation',
        'logs',
        'logs/audit',
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            print("\n⚠️  Creating .env file from template...")
            print("📝 Please edit .env and add your API keys:")
            print("   - GEMINI_API_KEY")
            print("   - OPENWEATHER_API_KEY")
            print("   - GEE_PROJECT_ID (optional)")
            
            # Copy template
            with open('.env.example', 'r') as template:
                with open('.env', 'w') as env_file:
                    env_file.write(template.read())
            print("✅ Created .env file")
        else:
            print("❌ .env.example not found!")
    else:
        print("✅ .env file already exists")

def check_api_keys():
    """Check if API keys are configured"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        print("\n🔑 Checking API Keys...")
        
        gemini_key = os.getenv('GEMINI_API_KEY')
        weather_key = os.getenv('OPENWEATHER_API_KEY')
        
        if gemini_key and gemini_key != 'your_gemini_api_key_here':
            print("✅ Gemini API key configured")
        else:
            print("⚠️  Gemini API key not configured - edit .env file")
        
        if weather_key and weather_key != 'your_openweather_api_key_here':
            print("✅ OpenWeather API key configured")
        else:
            print("⚠️  OpenWeather API key not configured - edit .env file")
            
    except ImportError:
        print("⚠️  python-dotenv not installed. Run: pip install -r requirements.txt")

def main():
    print("="*70)
    print("🌍 ClimateGuardAI - Quick Setup")
    print("="*70)
    
    # Step 1: Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Step 2: Setup .env
    print("\n🔧 Setting up environment variables...")
    create_env_file()
    
    # Step 3: Check API keys
    check_api_keys()
    
    print("\n" + "="*70)
    print("✅ Setup Complete!")
    print("="*70)
    print("\n📋 Next Steps:")
    print("1. Edit .env and add your API keys")
    print("2. Run: pip install -r requirements.txt")
    print("3. Run: python test_setup.py")
    print("4. Start backend: python src/api/main.py")
    print("5. Start frontend: streamlit run src/ui/app.py")
    print("\n🚀 Ready for ET Hackathon Round 2!")

if __name__ == "__main__":
    main()