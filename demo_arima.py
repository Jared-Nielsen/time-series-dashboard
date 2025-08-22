#!/usr/bin/env python3
"""
ARIMA Forecasting Demo
Demonstrates the ARIMA forecaster with real electricity price data
"""

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

def demo_arima_forecasting():
    print("="*70)
    print(" ARIMA ELECTRICITY PRICE FORECASTING DEMO")
    print("="*70)
    
    # Initialize data loader
    loader = DataLoader()
    
    # Try to load real data, fall back to sample if needed
    print("\n📊 Loading electricity price data...")
    try:
        # Try ERCOT first
        data = loader.load_ercot_data()
        if data is None or data.empty:
            raise ValueError("No ERCOT data available")
        data_source = "ERCOT (Texas)"
    except:
        # Fall back to sample data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=14)
        data = loader.load_sample_data(start_date=start_date, end_date=end_date, frequency='H')
        data_source = "Sample"
    
    print(f"✓ Loaded {len(data)} hours of {data_source} data")
    print(f"  Date range: {data.index[0]} to {data.index[-1]}")
    print(f"  Price range: ${data['price_per_mwh'].min():.2f} - ${data['price_per_mwh'].max():.2f}")
    print(f"  Mean price: ${data['price_per_mwh'].mean():.2f}")
    
    # Split data into train and test
    train_size = min(24*7*2, int(len(data) * 0.8))  # 2 weeks or 80%
    test_size = min(24*3, len(data) - train_size)   # 3 days for testing
    
    train_data = data['price_per_mwh'][:train_size]
    test_data = data['price_per_mwh'][train_size:train_size+test_size]
    
    print(f"\n📈 Data split:")
    print(f"  Training: {len(train_data)} hours ({len(train_data)//24} days)")
    print(f"  Testing: {len(test_data)} hours ({len(test_data)//24} days)")
    
    # Create and fit ARIMA model
    print("\n🔧 Fitting ARIMA model...")
    print("  Auto-selecting optimal parameters...")
    
    forecaster = ARIMAForecaster(
        seasonal=True,
        seasonal_period=24,  # Daily seasonality for hourly data
        auto_select=True,
        max_p=3,
        max_q=3,
        max_d=2,
        max_P=2,
        max_Q=2,
        information_criterion='aic'
    )
    
    # Fit the model
    forecaster.fit(train_data)
    
    # Get model parameters
    params = forecaster.get_params()
    print(f"\n✓ Model fitted successfully!")
    print(f"  Model type: {params['model_type']}")
    print(f"  Order (p,d,q): {params['order']}")
    if params['seasonal_order']:
        print(f"  Seasonal order (P,D,Q,s): {params['seasonal_order']}")
    print(f"  AIC: {params['aic']:.2f}")
    print(f"  BIC: {params['bic']:.2f}")
    
    # Generate forecasts
    print(f"\n🔮 Generating {len(test_data)}-hour forecast...")
    forecast_result = forecaster.forecast(steps=len(test_data), return_conf_int=True)
    
    forecast_values = forecast_result['forecast']
    lower_bound = forecast_result['lower_bound']
    upper_bound = forecast_result['upper_bound']
    
    # Calculate metrics
    mae = mean_absolute_error(test_data, forecast_values)
    rmse = np.sqrt(mean_squared_error(test_data, forecast_values))
    mape = np.mean(np.abs((test_data.values - forecast_values.values) / test_data.values)) * 100
    
    # Calculate directional accuracy
    actual_direction = np.diff(test_data.values) > 0
    forecast_direction = np.diff(forecast_values.values) > 0
    directional_accuracy = np.mean(actual_direction == forecast_direction) * 100
    
    print("\n📊 Forecast Performance Metrics:")
    print(f"  MAE: ${mae:.2f}/MWh")
    print(f"  RMSE: ${rmse:.2f}/MWh")
    print(f"  MAPE: {mape:.1f}%")
    print(f"  Directional Accuracy: {directional_accuracy:.1f}%")
    
    # Check confidence interval coverage
    coverage = np.mean((test_data.values >= lower_bound.values) & 
                      (test_data.values <= upper_bound.values)) * 100
    print(f"  95% CI Coverage: {coverage:.1f}%")
    
    # Create visualization
    print("\n📈 Creating visualization...")
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    
    # Plot 1: Forecast vs Actual
    axes[0].plot(train_data.index[-48:], train_data.values[-48:], 
                label='Historical', color='blue', alpha=0.7)
    axes[0].plot(test_data.index, test_data.values, 
                label='Actual', color='green', linewidth=2)
    axes[0].plot(test_data.index, forecast_values, 
                label='Forecast', color='red', linewidth=2, linestyle='--')
    axes[0].fill_between(test_data.index, lower_bound, upper_bound, 
                         alpha=0.3, color='red', label='95% CI')
    axes[0].set_title(f'ARIMA Forecast: {data_source} Electricity Prices', fontsize=14)
    axes[0].set_ylabel('Price ($/MWh)')
    axes[0].legend(loc='upper left')
    axes[0].grid(True, alpha=0.3)
    
    # Plot 2: Forecast Errors
    errors = test_data.values - forecast_values.values
    axes[1].bar(range(len(errors)), errors, color=['red' if e > 0 else 'green' for e in errors], alpha=0.7)
    axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    axes[1].set_title('Forecast Errors (Actual - Forecast)', fontsize=12)
    axes[1].set_xlabel('Hour')
    axes[1].set_ylabel('Error ($/MWh)')
    axes[1].grid(True, alpha=0.3)
    
    # Plot 3: Error Distribution
    axes[2].hist(errors, bins=20, edgecolor='black', alpha=0.7, color='blue')
    axes[2].axvline(x=0, color='red', linestyle='--', alpha=0.5)
    axes[2].set_title('Distribution of Forecast Errors', fontsize=12)
    axes[2].set_xlabel('Error ($/MWh)')
    axes[2].set_ylabel('Frequency')
    
    # Add statistics to the plot
    axes[2].text(0.02, 0.98, f'Mean: ${np.mean(errors):.2f}\nStd: ${np.std(errors):.2f}', 
                transform=axes[2].transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the plot
    output_file = 'arima_forecast_demo.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Visualization saved as '{output_file}'")
    
    # Model diagnostics
    print("\n🔍 Model Diagnostics:")
    diagnostics = forecaster.get_model_diagnostics()
    print(f"  Residual mean: {diagnostics['residual_mean']:.4f}")
    print(f"  Residual std: ${diagnostics['residual_std']:.2f}")
    
    # Check for residual autocorrelation
    ljung_box = diagnostics['ljung_box']
    min_pvalue = ljung_box['lb_pvalue'].min()
    if min_pvalue > 0.05:
        print(f"  ✓ Residuals appear to be white noise (p-value: {min_pvalue:.3f})")
    else:
        print(f"  ⚠ Residuals show autocorrelation (p-value: {min_pvalue:.3f})")
    
    # Backtesting demonstration
    print("\n🔄 Running backtesting (walk-forward validation)...")
    if len(data) >= 24*10:  # Need at least 10 days
        rolling_result = forecaster.rolling_forecast(
            data=data['price_per_mwh'][:min(24*14, len(data))],  # Use up to 2 weeks
            initial_train_size=24*5,  # 5 days initial training
            horizon=24,  # 24-hour forecast
            step_size=24,  # Move forward 1 day at a time
            refit_interval=24*2  # Refit every 2 days
        )
        
        all_forecasts = rolling_result['forecasts'].flatten()
        all_actuals = rolling_result['actuals'].flatten()
        
        backtest_mae = mean_absolute_error(all_actuals, all_forecasts)
        backtest_rmse = np.sqrt(mean_squared_error(all_actuals, all_forecasts))
        
        print(f"  Windows tested: {rolling_result['n_windows']}")
        print(f"  Backtest MAE: ${backtest_mae:.2f}/MWh")
        print(f"  Backtest RMSE: ${backtest_rmse:.2f}/MWh")
    
    print("\n" + "="*70)
    print(" ✅ ARIMA FORECASTING DEMO COMPLETE!")
    print("="*70)
    
    return forecaster, forecast_result

if __name__ == "__main__":
    forecaster, results = demo_arima_forecasting()
    print("\n💡 Tip: The ARIMA model is now ready to be integrated into the dashboard!")