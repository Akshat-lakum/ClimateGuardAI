import os
import requests
from dotenv import load_dotenv  

load_dotenv() 
api_key = os.getenv("OPENWEATHER_API_KEY")

if not api_key:
    print("❌ OPENWEATHER_API_KEY not found!")
    print("Check that your .env file is in the same folder as this script.")
    exit(1)

url = "https://api.openweathermap.org/data/2.5/weather"
params = {
    'lat': 19.0760,
    'lon': 72.8777,
    'appid': api_key,
    'units': 'metric'
}

print("Testing OpenWeather API...")
try:
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        print(f"✅ Weather API Working!")
        print(f"Mumbai Temperature: {temp}°C")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Connection Failed: {e}")