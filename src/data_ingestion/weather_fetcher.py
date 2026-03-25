"""
Weather Data Ingestion Module
Fetches real-time and forecast weather data from multiple sources
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
import asyncio
import aiohttp


class WeatherDataFetcher:
    """Fetches weather data from OpenWeatherMap and IMD"""
    
    def __init__(self, api_key: str):
        """
        Initialize weather fetcher
        
        Args:
            api_key: OpenWeatherMap API key
        """
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.imd_url = "https://mausam.imd.gov.in"
    
    def get_current_weather(self, latitude: float, longitude: float) -> Dict:
        """
        Get current weather conditions
        
        Args:
            latitude: Latitude of location
            longitude: Longitude of location
            
        Returns:
            Current weather data
        """
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            weather_data = {
                'timestamp': datetime.fromtimestamp(data['dt']),
                'location': {
                    'name': data.get('name', 'Unknown'),
                    'lat': latitude,
                    'lon': longitude
                },
                'temperature': {
                    'current': data['main']['temp'],
                    'feels_like': data['main']['feels_like'],
                    'min': data['main']['temp_min'],
                    'max': data['main']['temp_max']
                },
                'pressure': data['main']['pressure'],
                'humidity': data['main']['humidity'],
                'wind': {
                    'speed': data['wind']['speed'],
                    'direction': data['wind'].get('deg', 0)
                },
                'clouds': data['clouds']['all'],
                'description': data['weather'][0]['description'],
                'weather_condition': data['weather'][0]['main']
            }
            
            if 'rain' in data:
                weather_data['rainfall'] = data['rain'].get('1h', 0)
            
            logger.info(f"Fetched current weather for {latitude}, {longitude}")
            return weather_data
            
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            return None
    
    def get_forecast(
        self, 
        latitude: float, 
        longitude: float, 
        days: int = 7
    ) -> pd.DataFrame:
        """
        Get weather forecast
        
        Args:
            latitude: Latitude
            longitude: Longitude
            days: Number of forecast days
            
        Returns:
            DataFrame with forecast data
        """
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric',
                'cnt': days * 8  # 3-hour intervals
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            forecast_list = []
            for item in data['list']:
                forecast_list.append({
                    'timestamp': datetime.fromtimestamp(item['dt']),
                    'temperature': item['main']['temp'],
                    'temp_min': item['main']['temp_min'],
                    'temp_max': item['main']['temp_max'],
                    'pressure': item['main']['pressure'],
                    'humidity': item['main']['humidity'],
                    'wind_speed': item['wind']['speed'],
                    'clouds': item['clouds']['all'],
                    'description': item['weather'][0]['description'],
                    'rain_3h': item.get('rain', {}).get('3h', 0)
                })
            
            df = pd.DataFrame(forecast_list)
            logger.info(f"Fetched {len(df)} forecast records")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            return pd.DataFrame()
    
    def get_historical_weather(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Get historical weather data (requires paid API)
        
        Args:
            latitude: Latitude
            longitude: Longitude
            start_date: Start date
            end_date: End date
            
        Returns:
            Historical weather DataFrame
        """
        try:
            # Note: This requires OpenWeatherMap History API (paid)
            # For hackathon, we'll simulate or use free alternatives
            
            logger.warning("Historical API not implemented - using simulated data")
            
            # Generate date range
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # For demo: create synthetic data
            # In production, use actual historical API
            data = []
            for date in dates:
                data.append({
                    'date': date,
                    'temperature': 25 + (date.dayofyear % 30) / 3,  # Synthetic
                    'humidity': 60 + (date.dayofyear % 20),
                    'rainfall': max(0, 10 - abs(date.dayofyear % 30 - 15))
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error fetching historical weather: {e}")
            return pd.DataFrame()
    
    async def get_multi_location_weather(
        self,
        locations: List[Dict[str, float]]
    ) -> List[Dict]:
        """
        Async fetch weather for multiple locations
        
        Args:
            locations: List of dicts with 'lat' and 'lon'
            
        Returns:
            List of weather data
        """
        async with aiohttp.ClientSession() as session:
            tasks = []
            for loc in locations:
                task = self._fetch_async(
                    session, 
                    loc['lat'], 
                    loc['lon']
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            return results
    
    async def _fetch_async(
        self,
        session: aiohttp.ClientSession,
        latitude: float,
        longitude: float
    ) -> Dict:
        """Async helper for fetching weather"""
        url = f"{self.base_url}/weather"
        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            async with session.get(url, params=params) as response:
                data = await response.json()
                return {
                    'location': {'lat': latitude, 'lon': longitude},
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity']
                }
        except Exception as e:
            logger.error(f"Async fetch error: {e}")
            return None
    
    def get_weather_alerts(
        self,
        latitude: float,
        longitude: float
    ) -> List[Dict]:
        """
        Get active weather alerts
        
        Args:
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            List of active alerts
        """
        try:
            url = f"{self.base_url}/onecall"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'exclude': 'minutely,hourly'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'alerts' in data:
                alerts = []
                for alert in data['alerts']:
                    alerts.append({
                        'event': alert['event'],
                        'start': datetime.fromtimestamp(alert['start']),
                        'end': datetime.fromtimestamp(alert['end']),
                        'description': alert['description'],
                        'sender': alert.get('sender_name', 'Unknown')
                    })
                return alerts
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching weather alerts: {e}")
            return []
    
    def aggregate_daily_forecast(self, forecast_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate 3-hourly forecast to daily
        
        Args:
            forecast_df: 3-hourly forecast DataFrame
            
        Returns:
            Daily aggregated forecast
        """
        if forecast_df.empty:
            return pd.DataFrame()
        
        # Extract date
        forecast_df['date'] = forecast_df['timestamp'].dt.date
        
        # Aggregate by day
        daily = forecast_df.groupby('date').agg({
            'temperature': 'mean',
            'temp_min': 'min',
            'temp_max': 'max',
            'humidity': 'mean',
            'wind_speed': 'mean',
            'rain_3h': 'sum'
        }).reset_index()
        
        daily.rename(columns={'rain_3h': 'total_rainfall'}, inplace=True)
        
        return daily


# Example usage
if __name__ == "__main__":
    from configs.config import settings
    
    fetcher = WeatherDataFetcher(api_key=settings.openweather_api_key)
    
    # Test location
    lat, lon = 19.0760, 72.8777  # Mumbai
    
    # Get current weather
    current = fetcher.get_current_weather(lat, lon)
    print("Current Weather:", current)
    
    # Get forecast
    forecast = fetcher.get_forecast(lat, lon, days=7)
    print("\nForecast:")
    print(forecast.head())
    
    # Aggregate to daily
    daily_forecast = fetcher.aggregate_daily_forecast(forecast)
    print("\nDaily Forecast:")
    print(daily_forecast)