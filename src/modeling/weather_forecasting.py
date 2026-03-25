"""
Weather Forecasting Model using Temporal Fusion Transformer (TFT)
"""
import torch
import pytorch_lightning as pl
from pytorch_forecasting import TimeSeriesDataSet, TemporalFusionTransformer
from pytorch_forecasting.data import GroupNormalizer
from pytorch_forecasting.metrics import QuantileLoss
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from loguru import logger
from pathlib import Path


class WeatherForecaster:
    """Weather forecasting using TFT model"""
    
    def __init__(
        self,
        max_encoder_length: int = 30,
        max_prediction_length: int = 7,
        model_path: str = None
    ):
        """
        Initialize forecaster
        
        Args:
            max_encoder_length: Number of historical days to use
            max_prediction_length: Number of days to forecast
            model_path: Path to saved model
        """
        self.max_encoder_length = max_encoder_length
        self.max_prediction_length = max_prediction_length
        self.model_path = model_path
        self.model = None
        self.training_dataset = None
    
    def prepare_data(
        self,
        weather_data: pd.DataFrame,
        satellite_data: pd.DataFrame = None
    ) -> TimeSeriesDataSet:
        """
        Prepare time series data for TFT
        
        Args:
            weather_data: DataFrame with columns: date, location_id, temperature, humidity, rainfall, etc.
            satellite_data: Optional satellite indices (NDVI, NDWI)
            
        Returns:
            TimeSeriesDataSet for training
        """
        try:
            # Ensure data is sorted
            weather_data = weather_data.sort_values(['location_id', 'date'])
            
            # Add time index
            weather_data['time_idx'] = (
                weather_data.groupby('location_id')['date']
                .apply(lambda x: (x - x.min()).dt.days)
            )
            
            # Add temporal features
            weather_data['month'] = weather_data['date'].dt.month
            weather_data['day_of_year'] = weather_data['date'].dt.dayofyear
            weather_data['week_of_year'] = weather_data['date'].dt.isocalendar().week
            
            # Merge satellite data if provided
            if satellite_data is not None:
                weather_data = weather_data.merge(
                    satellite_data,
                    on=['location_id', 'date'],
                    how='left'
                )
            
            # Define time-varying known features (future is known)
            time_varying_known_reals = ['time_idx', 'month', 'day_of_year']
            
            # Time-varying unknown features (to be predicted)
            time_varying_unknown_reals = [
                'temperature', 'humidity', 'rainfall', 'wind_speed'
            ]
            
            # Add satellite indices if available
            if satellite_data is not None:
                time_varying_unknown_reals.extend(['ndvi', 'ndwi'])
            
            # Static features (don't change over time)
            static_categoricals = ['location_id']
            
            # Create dataset
            dataset = TimeSeriesDataSet(
                weather_data,
                time_idx='time_idx',
                target='temperature',  # Primary target
                group_ids=['location_id'],
                min_encoder_length=self.max_encoder_length // 2,
                max_encoder_length=self.max_encoder_length,
                min_prediction_length=1,
                max_prediction_length=self.max_prediction_length,
                static_categoricals=static_categoricals,
                time_varying_known_reals=time_varying_known_reals,
                time_varying_unknown_reals=time_varying_unknown_reals,
                target_normalizer=GroupNormalizer(
                    groups=['location_id'],
                    transformation='softplus'
                ),
                add_relative_time_idx=True,
                add_target_scales=True,
                add_encoder_length=True,
            )
            
            self.training_dataset = dataset
            logger.info(f"Prepared dataset with {len(weather_data)} records")
            return dataset
            
        except Exception as e:
            logger.error(f"Error preparing data: {e}")
            raise
    
    def train(
        self,
        train_dataloader,
        val_dataloader,
        max_epochs: int = 50,
        gpus: int = 0
    ) -> TemporalFusionTransformer:
        """
        Train TFT model
        
        Args:
            train_dataloader: Training data loader
            val_dataloader: Validation data loader
            max_epochs: Maximum training epochs
            gpus: Number of GPUs to use
            
        Returns:
            Trained model
        """
        try:
            # Create trainer
            trainer = pl.Trainer(
                max_epochs=max_epochs,
                gpus=gpus,
                gradient_clip_val=0.1,
                callbacks=[
                    pl.callbacks.EarlyStopping(
                        monitor='val_loss',
                        patience=5,
                        mode='min'
                    )
                ]
            )
            
            # Initialize model
            tft = TemporalFusionTransformer.from_dataset(
                self.training_dataset,
                learning_rate=0.03,
                hidden_size=32,
                attention_head_size=2,
                dropout=0.1,
                hidden_continuous_size=16,
                output_size=7,  # 7 quantiles for probabilistic forecasting
                loss=QuantileLoss(),
                log_interval=10,
                reduce_on_plateau_patience=4
            )
            
            # Train
            logger.info("Starting model training...")
            trainer.fit(
                tft,
                train_dataloaders=train_dataloader,
                val_dataloaders=val_dataloader
            )
            
            self.model = tft
            
            # Save model
            if self.model_path:
                self.save_model(self.model_path)
            
            logger.info("Model training completed")
            return tft
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    def predict(
        self,
        encoder_data: pd.DataFrame,
        location_id: str
    ) -> Dict:
        """
        Make predictions for a location
        
        Args:
            encoder_data: Historical data for encoding
            location_id: Location identifier
            
        Returns:
            Predictions dictionary
        """
        if self.model is None:
            if self.model_path and Path(self.model_path).exists():
                self.load_model(self.model_path)
            else:
                raise ValueError("No trained model available")
        
        try:
            # Prepare encoder data
            encoder_data = encoder_data[
                encoder_data['location_id'] == location_id
            ].tail(self.max_encoder_length)
            
            # Make prediction
            raw_predictions = self.model.predict(
                encoder_data,
                mode='raw',
                return_x=True
            )
            
            # Extract predictions
            predictions = raw_predictions.output.prediction
            
            # Get quantiles (median, upper/lower bounds)
            median_pred = predictions[:, :, 3].numpy()  # 50th percentile
            lower_bound = predictions[:, :, 1].numpy()  # 10th percentile
            upper_bound = predictions[:, :, 5].numpy()  # 90th percentile
            
            result = {
                'forecast_days': self.max_prediction_length,
                'median': median_pred[0].tolist(),
                'lower_bound': lower_bound[0].tolist(),
                'upper_bound': upper_bound[0].tolist(),
                'confidence_interval': 80  # 10th to 90th percentile
            }
            
            logger.info(f"Generated forecast for location {location_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise
    
    def save_model(self, path: str):
        """Save trained model"""
        if self.model is not None:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            torch.save(self.model.state_dict(), path)
            logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load trained model"""
        if self.training_dataset is None:
            raise ValueError("Training dataset required to load model architecture")
        
        self.model = TemporalFusionTransformer.from_dataset(
            self.training_dataset,
            learning_rate=0.03,
            hidden_size=32,
            attention_head_size=2,
            dropout=0.1,
            hidden_continuous_size=16,
            output_size=7,
            loss=QuantileLoss()
        )
        
        self.model.load_state_dict(torch.load(path))
        self.model.eval()
        logger.info(f"Model loaded from {path}")


class SimpleForecaster:
    """Simplified forecasting using Prophet (for quick prototyping)"""
    
    def __init__(self):
        """Initialize Prophet-based forecaster"""
        from prophet import Prophet
        self.model = Prophet(
            changepoint_prior_scale=0.05,
            seasonality_mode='multiplicative'
        )
    
    def train(self, data: pd.DataFrame):
        """
        Train Prophet model
        
        Args:
            data: DataFrame with 'ds' (date) and 'y' (value) columns
        """
        self.model.fit(data)
        logger.info("Prophet model trained")
    
    def predict(self, periods: int = 7) -> pd.DataFrame:
        """
        Make forecast
        
        Args:
            periods: Number of days to forecast
            
        Returns:
            Forecast DataFrame
        """
        future = self.model.make_future_dataframe(periods=periods)
        forecast = self.model.predict(future)
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)


# Example usage
if __name__ == "__main__":
    # Generate sample data
    np.random.seed(42)
    
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    locations = ['LOC_1', 'LOC_2', 'LOC_3']
    
    data = []
    for loc in locations:
        for i, date in enumerate(dates):
            data.append({
                'date': date,
                'location_id': loc,
                'temperature': 25 + 10 * np.sin(2 * np.pi * i / 365) + np.random.randn(),
                'humidity': 60 + 20 * np.sin(2 * np.pi * i / 365 + np.pi/4) + np.random.randn() * 5,
                'rainfall': max(0, 10 + 5 * np.sin(2 * np.pi * i / 365 + np.pi/2) + np.random.randn() * 3),
                'wind_speed': 15 + 5 * np.random.randn()
            })
    
    df = pd.DataFrame(data)
    
    # Train model
    forecaster = WeatherForecaster()
    dataset = forecaster.prepare_data(df)
    
    print("Dataset prepared successfully!")
    print(f"Number of samples: {len(dataset)}")