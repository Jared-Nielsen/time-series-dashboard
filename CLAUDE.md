# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Time Series Forecasting Dashboard for electricity price prediction, currently in initial development phase. The application will provide both econometric (ARIMA) and machine learning (LSTM) forecasting capabilities with an interactive web interface.

## Development Setup

### Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies (once requirements.txt is created)
pip install -r requirements.txt
```

### Core Dependencies to Install
When implementing features, these are the main packages needed:
- `streamlit` or `dash` - for dashboard interface
- `pandas`, `numpy` - data processing
- `statsmodels` - ARIMA implementation
- `tensorflow` or `pytorch` - LSTM implementation
- `plotly` - interactive visualizations
- `scikit-learn` - model evaluation metrics
- `openpyxl`, `xlrd` - Excel file support

## Architecture Guidelines

### Project Structure (Recommended)
```
time-series-dashboard/
├── src/
│   ├── data/
│   │   ├── loader.py         # Data loading and validation
│   │   └── preprocessor.py   # Data preprocessing and feature engineering
│   ├── models/
│   │   ├── arima.py         # ARIMA model implementation
│   │   └── lstm.py          # LSTM model implementation
│   ├── evaluation/
│   │   ├── metrics.py       # MAE, RMSE, MAPE calculations
│   │   └── backtesting.py   # Walk-forward validation
│   ├── visualization/
│   │   └── plots.py         # Plotly chart generators
│   └── app.py              # Main Streamlit/Dash application
├── tests/
├── data/                   # Sample data directory
└── requirements.txt
```

### Key Implementation Priorities

1. **Data Processing Pipeline**: Handle CSV/Excel uploads with validation for time series data (timestamps + prices)
2. **Model Modularity**: Keep ARIMA and LSTM implementations separate and interchangeable
3. **Forecast Comparison**: Ensure both models output compatible forecast formats for side-by-side comparison
4. **Backtesting Framework**: Implement walk-forward validation with configurable window sizes
5. **Error Handling**: Robust handling of data quality issues (missing values, outliers)

## Testing Commands

Once test framework is set up:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_models.py
```

## Key Features from PRD

- **Data Upload**: Support CSV/Excel with timestamp and price columns
- **ARIMA Forecasting**: Using statsmodels with automatic parameter selection (consider auto-ARIMA)
- **LSTM Forecasting**: Multi-layer LSTM with proper sequence preparation
- **Interactive Dashboard**: Real-time parameter adjustment and visualization updates
- **Backtesting**: Walk-forward validation with holdout periods
- **Metrics**: MAE, RMSE, MAPE for model comparison
- **Export**: Download forecasts and performance metrics

## Important Considerations

- **Data Frequency**: Support hourly, daily, weekly, monthly electricity price data
- **Forecast Horizons**: Configurable from 1 to 30+ periods ahead
- **Performance**: Cache model results for large datasets
- **Visualization**: Use Plotly for interactive charts with zoom/pan capabilities
- **State Management**: If using Streamlit, careful session state management for model persistence