"""
Google Earth Engine Data Ingestion Module
Fetches satellite imagery and environmental data
"""
import ee
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from loguru import logger
import json


class EarthEngineClient:
    """Client for fetching satellite data from Google Earth Engine"""
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Earth Engine client
        
        Args:
            project_id: GEE project ID (optional if using service account)
        """
        try:
            # Authenticate and initialize
            if project_id:
                ee.Initialize(project=project_id)
            else:
                ee.Initialize()
            logger.info("Google Earth Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Earth Engine: {e}")
            raise
    
    def get_sentinel2_data(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str,
        buffer_km: int = 5
    ) -> Dict:
        """
        Fetch Sentinel-2 satellite imagery for a location
        
        Args:
            latitude: Latitude of location
            longitude: Longitude of location
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            buffer_km: Buffer around point in kilometers
            
        Returns:
            Dictionary with NDVI, NDWI, and other indices
        """
        try:
            # Define point and buffer
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(buffer_km * 1000)  # Convert km to meters
            
            # Load Sentinel-2 collection
            collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                         .filterBounds(point)
                         .filterDate(start_date, end_date)
                         .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))
            
            if collection.size().getInfo() == 0:
                logger.warning(f"No Sentinel-2 images found for {latitude}, {longitude}")
                return None
            
            # Get median composite
            image = collection.median()
            
            # Calculate vegetation indices
            ndvi = self._calculate_ndvi(image)
            ndwi = self._calculate_ndwi(image)
            evi = self._calculate_evi(image)
            
            # Get statistics for the region
            ndvi_stats = self._get_reduction_stats(ndvi, region, 'NDVI')
            ndwi_stats = self._get_reduction_stats(ndwi, region, 'NDWI')
            evi_stats = self._get_reduction_stats(evi, region, 'EVI')
            
            # Get RGB thumbnail
            thumbnail_url = self._get_thumbnail_url(image, region)
            
            result = {
                'location': {'lat': latitude, 'lon': longitude},
                'date_range': {'start': start_date, 'end': end_date},
                'ndvi': ndvi_stats,
                'ndwi': ndwi_stats,
                'evi': evi_stats,
                'thumbnail_url': thumbnail_url,
                'image_count': collection.size().getInfo()
            }
            
            logger.info(f"Successfully fetched Sentinel-2 data for {latitude}, {longitude}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching Sentinel-2 data: {e}")
            return None
    
    def get_landsat_temperature(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        buffer_km: int = 5
    ) -> Dict:
        """
        Fetch land surface temperature from Landsat
        
        Args:
            latitude: Latitude of location
            longitude: Longitude of location
            start_date: Start date
            end_date: End date
            buffer_km: Buffer in kilometers
            
        Returns:
            Temperature statistics
        """
        try:
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(buffer_km * 1000)
            
            # Load Landsat 8 collection
            collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
                         .filterBounds(point)
                         .filterDate(start_date, end_date)
                         .filter(ee.Filter.lt('CLOUD_COVER', 20)))
            
            if collection.size().getInfo() == 0:
                return None
            
            # Get median composite
            image = collection.median()
            
            # Calculate land surface temperature
            lst = self._calculate_lst_landsat8(image)
            
            # Get statistics
            lst_stats = self._get_reduction_stats(lst, region, 'LST')
            
            result = {
                'location': {'lat': latitude, 'lon': longitude},
                'temperature_celsius': {
                    'mean': lst_stats['mean'] - 273.15,  # Convert to Celsius
                    'min': lst_stats['min'] - 273.15,
                    'max': lst_stats['max'] - 273.15,
                    'std': lst_stats['std']
                },
                'image_count': collection.size().getInfo()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching Landsat temperature: {e}")
            return None
    
    def get_precipitation_data(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Fetch historical precipitation data from CHIRPS
        
        Args:
            latitude: Latitude
            longitude: Longitude
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with daily precipitation
        """
        try:
            point = ee.Geometry.Point([longitude, latitude])
            
            # Load CHIRPS dataset
            chirps = (ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
                     .filterDate(start_date, end_date)
                     .select('precipitation'))
            
            # Convert to time series
            def extract_precip(image):
                value = image.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=point,
                    scale=5000
                ).get('precipitation')
                
                return ee.Feature(None, {
                    'date': image.date().format('YYYY-MM-dd'),
                    'precipitation': value
                })
            
            time_series = chirps.map(extract_precip)
            data = time_series.getInfo()
            
            # Convert to DataFrame
            records = []
            for feature in data['features']:
                records.append({
                    'date': feature['properties']['date'],
                    'precipitation_mm': feature['properties']['precipitation']
                })
            
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            
            logger.info(f"Fetched {len(df)} days of precipitation data")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching precipitation data: {e}")
            return pd.DataFrame()
    
    def _calculate_ndvi(self, image):
        """Calculate Normalized Difference Vegetation Index"""
        nir = image.select('B8')
        red = image.select('B4')
        ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
        return ndvi
    
    def _calculate_ndwi(self, image):
        """Calculate Normalized Difference Water Index"""
        nir = image.select('B8')
        swir = image.select('B11')
        ndwi = nir.subtract(swir).divide(nir.add(swir)).rename('NDWI')
        return ndwi
    
    def _calculate_evi(self, image):
        """Calculate Enhanced Vegetation Index"""
        nir = image.select('B8')
        red = image.select('B4')
        blue = image.select('B2')
        
        evi = image.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
            {
                'NIR': nir,
                'RED': red,
                'BLUE': blue
            }
        ).rename('EVI')
        return evi
    
    def _calculate_lst_landsat8(self, image):
        """Calculate Land Surface Temperature from Landsat 8"""
        # Thermal band (Band 10)
        thermal = image.select('ST_B10').multiply(0.00341802).add(149.0)
        return thermal.rename('LST')
    
    def _get_reduction_stats(self, image, region, band_name):
        """Get statistical reduction for a region"""
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                ee.Reducer.minMax(), '', True
            ).combine(
                ee.Reducer.stdDev(), '', True
            ),
            geometry=region,
            scale=10,
            maxPixels=1e9
        )
        
        result = stats.getInfo()
        return {
            'mean': result.get(f'{band_name}_mean'),
            'min': result.get(f'{band_name}_min'),
            'max': result.get(f'{band_name}_max'),
            'std': result.get(f'{band_name}_stdDev')
        }
    
    def _get_thumbnail_url(self, image, region):
        """Generate thumbnail URL for visualization"""
        vis_params = {
            'min': 0,
            'max': 3000,
            'bands': ['B4', 'B3', 'B2'],
            'region': region,
            'dimensions': 512
        }
        
        url = image.getThumbURL(vis_params)
        return url


# Example usage
if __name__ == "__main__":
    # Test the module
    from configs.config import settings
    
    client = EarthEngineClient(project_id=settings.gee_project_id)
    
    # Test location: Maharashtra, India
    lat, lon = 19.0760, 72.8777  # Mumbai
    
    # Fetch data for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    sentinel_data = client.get_sentinel2_data(
        latitude=lat,
        longitude=lon,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    print("Sentinel-2 Data:", json.dumps(sentinel_data, indent=2))