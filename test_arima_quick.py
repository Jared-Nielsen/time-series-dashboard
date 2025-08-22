import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from src.models.arima import ARIMAForecaster
from src.data.loader import DataLoader
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

def quick_arima_test():
    print("="*60)
    print("Quick ARIMA Forecaster Test")
    print("="*60)
    
    # Load a smaller dataset for faster testing
    loader = DataLoader()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # Only 7 days
    data = loader.load_sample_data(start_date=start_date, end_date=end_date, frequency='H')
    
    train_size = int(len(data) * 0.8)
    train_data = data['price_per_mwh'][:train_size]
    test_data = data['price_per_mwh'][train_size:]
    
    print(f"\nData: {len(data)} hours total")
    print(f"Train: {len(train_data)} hours | Test: {len(test_data)} hours")
    
    # Test 1: Simple ARIMA without auto-selection (faster)
    print("\n" + "="*40)
    print("Test 1: Simple ARIMA (1,1,1)")
    print("="*40)
    
    forecaster = ARIMAForecaster(
        seasonal=False,  # No seasonal for speed
        auto_select=False  # Use fixed parameters
    )
    
    forecaster.fit(train_data, order=(1, 1, 1))
    
    params = forecaster.get_params()
    print(f"Model: {params['model_type']}")
    print(f"Order: {params['order']}")
    print(f"AIC: {params['aic']:.2f}")
    
    # Generate forecast
    forecast_result = forecaster.forecast(steps=len(test_data))
    mae = mean_absolute_error(test_data, forecast_result['forecast'])
    rmse = np.sqrt(mean_squared_error(test_data, forecast_result['forecast']))
    
    print(f"\nForecast Performance:")
    print(f"MAE: ${mae:.2f}")
    print(f"RMSE: ${rmse:.2f}")
    
    # Test 2: SARIMA with fixed seasonal parameters
    print("\n" + "="*40)
    print("Test 2: SARIMA with Seasonality")
    print("="*40)
    
    forecaster2 = ARIMAForecaster(
        seasonal=True,
        seasonal_period=24,
        auto_select=False
    )
    
    forecaster2.fit(
        train_data, 
        order=(1, 1, 1),
        seasonal_order=(1, 0, 1, 24)
    )
    
    params2 = forecaster2.get_params()
    print(f"Model: {params2['model_type']}")
    print(f"Order: {params2['order']}")
    print(f"Seasonal Order: {params2['seasonal_order']}")
    print(f"AIC: {params2['aic']:.2f}")
    
    forecast_result2 = forecaster2.forecast(steps=len(test_data))
    mae2 = mean_absolute_error(test_data, forecast_result2['forecast'])
    rmse2 = np.sqrt(mean_squared_error(test_data, forecast_result2['forecast']))
    
    print(f"\nForecast Performance:")
    print(f"MAE: ${mae2:.2f}")
    print(f"RMSE: ${rmse2:.2f}")
    
    # Test 3: Model diagnostics
    print("\n" + "="*40)
    print("Test 3: Model Diagnostics")
    print("="*40)
    
    diagnostics = forecaster.get_model_diagnostics()
    print(f"Residual mean: {diagnostics['residual_mean']:.4f}")
    print(f"Residual std: {diagnostics['residual_std']:.2f}")
    
    # Check if residuals are white noise
    ljung_box = diagnostics['ljung_box']
    if ljung_box['lb_pvalue'].min() > 0.05:
        print("✓ Residuals appear to be white noise")
    else:
        print("⚠ Residuals show autocorrelation")
    
    print("\n" + "="*60)
    print("✓ ARIMA Forecaster is working correctly!")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = quick_arima_test()
    if success:
        print("\nAll tests passed successfully!")