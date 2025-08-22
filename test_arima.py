import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from src.models.arima import ARIMAForecaster
from src.data.loader import DataLoader
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

def test_arima_with_sample_data():
    print("="*60)
    print("Testing ARIMA Forecaster with Sample Electricity Data")
    print("="*60)
    
    loader = DataLoader()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    data = loader.load_sample_data(start_date=start_date, end_date=end_date, frequency='H')
    
    train_size = int(len(data) * 0.8)
    train_data = data['price_per_mwh'][:train_size]
    test_data = data['price_per_mwh'][train_size:]
    
    print(f"\nData shape: {len(data)} hours")
    print(f"Training size: {len(train_data)} hours")
    print(f"Test size: {len(test_data)} hours")
    print(f"Price range: ${data['price_per_mwh'].min():.2f} - ${data['price_per_mwh'].max():.2f}")
    
    print("\n" + "="*40)
    print("1. Testing Auto-ARIMA Parameter Selection")
    print("="*40)
    
    forecaster = ARIMAForecaster(
        seasonal=True,
        auto_select=True,
        max_p=3,
        max_q=3,
        max_d=2,
        max_P=2,
        max_Q=2,
        information_criterion='aic'
    )
    
    forecaster.fit(train_data)
    
    params = forecaster.get_params()
    print(f"Selected model: {params['model_type']}")
    print(f"Order (p,d,q): {params['order']}")
    if params['seasonal_order']:
        print(f"Seasonal order (P,D,Q,s): {params['seasonal_order']}")
    print(f"AIC: {params['aic']:.2f}")
    print(f"BIC: {params['bic']:.2f}")
    
    print("\n" + "="*40)
    print("2. Generating Forecast")
    print("="*40)
    
    forecast_steps = len(test_data)
    forecast_result = forecaster.forecast(steps=forecast_steps, return_conf_int=True)
    
    print(f"Forecast horizon: {forecast_steps} hours")
    print(f"Confidence level: {forecast_result['confidence_level']*100}%")
    
    forecast_values = forecast_result['forecast']
    lower_bound = forecast_result['lower_bound']
    upper_bound = forecast_result['upper_bound']
    
    mae = mean_absolute_error(test_data, forecast_values)
    rmse = np.sqrt(mean_squared_error(test_data, forecast_values))
    mape = np.mean(np.abs((test_data.values - forecast_values.values) / test_data.values)) * 100
    
    print(f"\nForecast Performance:")
    print(f"MAE: ${mae:.2f}")
    print(f"RMSE: ${rmse:.2f}")
    print(f"MAPE: {mape:.2f}%")
    
    print("\n" + "="*40)
    print("3. Model Diagnostics")
    print("="*40)
    
    diagnostics = forecaster.get_model_diagnostics()
    print(f"Residual mean: {diagnostics['residual_mean']:.4f}")
    print(f"Residual std: {diagnostics['residual_std']:.2f}")
    
    ljung_box = diagnostics['ljung_box']
    print(f"\nLjung-Box Test (p-values for lags 1-10):")
    print(f"Min p-value: {ljung_box['lb_pvalue'].min():.4f}")
    if ljung_box['lb_pvalue'].min() > 0.05:
        print("✓ No significant autocorrelation in residuals")
    else:
        print("⚠ Significant autocorrelation detected in residuals")
    
    print("\n" + "="*40)
    print("4. Visualizing Results")
    print("="*40)
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    axes[0].plot(train_data.index, train_data.values, label='Training Data', color='blue', alpha=0.7)
    axes[0].plot(test_data.index, test_data.values, label='Actual Test Data', color='green', alpha=0.7)
    axes[0].plot(test_data.index, forecast_values, label='Forecast', color='red', alpha=0.8)
    axes[0].fill_between(test_data.index, lower_bound, upper_bound, alpha=0.2, color='red', label='95% CI')
    axes[0].set_title('ARIMA Forecast vs Actual')
    axes[0].set_ylabel('Price ($)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    residuals = test_data.values - forecast_values.values
    axes[1].plot(test_data.index, residuals, marker='o', linestyle='-', alpha=0.7)
    axes[1].axhline(y=0, color='red', linestyle='--', alpha=0.5)
    axes[1].set_title('Forecast Errors (Residuals)')
    axes[1].set_ylabel('Error ($)')
    axes[1].grid(True, alpha=0.3)
    
    axes[2].hist(residuals, bins=20, edgecolor='black', alpha=0.7)
    axes[2].set_title('Distribution of Forecast Errors')
    axes[2].set_xlabel('Error ($)')
    axes[2].set_ylabel('Frequency')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('arima_forecast_results.png', dpi=150, bbox_inches='tight')
    print("Visualization saved as 'arima_forecast_results.png'")
    
    print("\n" + "="*40)
    print("5. Testing Rolling Forecast (Backtesting)")
    print("="*40)
    
    full_data = data['price_per_mwh']
    rolling_result = forecaster.rolling_forecast(
        data=full_data,
        initial_train_size=24*7,  
        horizon=24,  
        step_size=24,  
        refit_interval=24*3  
    )
    
    print(f"Number of forecast windows: {rolling_result['n_windows']}")
    print(f"Forecast horizon per window: {rolling_result['horizon']} hours")
    
    all_forecasts = rolling_result['forecasts'].flatten()
    all_actuals = rolling_result['actuals'].flatten()
    
    rolling_mae = mean_absolute_error(all_actuals, all_forecasts)
    rolling_rmse = np.sqrt(mean_squared_error(all_actuals, all_forecasts))
    rolling_mape = np.mean(np.abs((all_actuals - all_forecasts) / all_actuals)) * 100
    
    print(f"\nRolling Forecast Performance:")
    print(f"MAE: ${rolling_mae:.2f}")
    print(f"RMSE: ${rolling_rmse:.2f}")
    print(f"MAPE: {rolling_mape:.2f}%")
    
    coverage = np.mean(
        (all_actuals >= rolling_result['lower_bounds'].flatten()) & 
        (all_actuals <= rolling_result['upper_bounds'].flatten())
    )
    print(f"95% CI Coverage: {coverage*100:.1f}%")
    
    print("\n" + "="*60)
    print("ARIMA Forecaster Test Complete!")
    print("="*60)

def test_with_real_data():
    print("\n" + "="*60)
    print("Testing with Real ERCOT Data")
    print("="*60)
    
    loader = DataLoader()
    try:
        data = loader.load_ercot_data()
        if data is not None and not data.empty:
            print(f"Loaded {len(data)} hours of ERCOT data")
            
            train_size = min(24*7, int(len(data) * 0.8))
            train_data = data['price_per_mwh'][:train_size]
            test_data = data['price_per_mwh'][train_size:train_size+24]
            
            forecaster = ARIMAForecaster(seasonal=True, seasonal_period=24, auto_select=True)
            forecaster.fit(train_data)
            
            forecast_result = forecaster.forecast(steps=len(test_data))
            mae = mean_absolute_error(test_data, forecast_result['forecast'])
            
            print(f"Model: {forecaster.get_params()['model_type']}")
            print(f"Order: {forecaster.get_params()['order']}")
            print(f"24-hour forecast MAE: ${mae:.2f}")
    except Exception as e:
        print(f"Could not test with real data: {e}")

if __name__ == "__main__":
    test_arima_with_sample_data()
    test_with_real_data()