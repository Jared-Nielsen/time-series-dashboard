# Time Series Dashboard - Electricity Price Forecasting

A comprehensive Python application for fetching, analyzing, and forecasting electricity prices using real-time data from US electricity markets.

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd time-series-dashboard

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the application
python main.py
```

## 📊 Features

- **Real-Time Data**: Live electricity prices from NYISO (New York) and ERCOT (Texas)
- **Multiple Data Sources**: Support for 5 major US ISOs/RTOs
- **Sample Data Generator**: Realistic synthetic data for testing
- **Data Validation**: Comprehensive validation and quality checks
- **Caching System**: Automatic local caching for performance
- **Export Options**: CSV and Parquet formats for analysis

## 🏃 How to Run and Test

### Option 1: Interactive Menu (Recommended)
```bash
python main.py
```
This launches an interactive menu where you can:
- Load real market data
- Generate sample data
- Export data for analysis
- View statistics
- Test specific ISOs

### Option 2: Quick Test All Sources
```bash
python test_iso_final.py
```
Tests all data sources and creates sample files.

### Option 3: Python Script
```python
from src.data.loader import DataLoader

loader = DataLoader()

# Get real electricity prices from New York
nyiso_data = loader.load_iso_data(iso='NYISO')

# Get real electricity prices from Texas
ercot_data = loader.load_iso_data(iso='ERCOT')

# Get all real market data
all_real_data = loader.load_iso_data(iso='all', include_simulated=False)

# Generate sample data for testing
sample_data = loader.load_sample_data()
```

### Option 4: Jupyter Notebook
```python
# In a Jupyter notebook
%run main.py
# Or import directly
from src.data.loader import DataLoader
loader = DataLoader()
df = loader.load_iso_data(iso='all')
df.head()
```

## 🧪 Testing Guide

### 1. Test All Data Sources
```bash
# Test that all ISOs are working
python test_all_isos.py

# Test just the real data sources
python test_iso_final.py
```

### 2. Test Individual Components
```bash
# Test ERCOT connection
python src/data/ercot_live.py

# Test ISO sources
python src/data/iso_sources_v2.py

# Test sample data generator
python test_data_sources.py
```

### 3. Validation Testing
```python
from src.data.loader import DataLoader

loader = DataLoader()
df = loader.load_sample_data()
validation = loader.validate_data(df)
print(f"Data valid: {validation['valid']}")
print(f"Issues: {validation['issues']}")
```

## 📁 Output Files

After running tests, you'll find:
- `real_iso_data.csv` - Combined real market data
- `data/iso_samples/` - Individual ISO data files
- `data/cache/` - Cached API responses
- `*.png` - Price comparison charts

## 🔌 Data Sources

| Source | Status | Type | Authentication |
|--------|--------|------|----------------|
| NYISO | ✅ Working | Real-time | None required |
| ERCOT | ✅ Working | Real-time | None required |
| Sample | ✅ Working | Synthetic | None required |
| PJM | ⚠️ Simulated | Requires registration | dataminer2.pjm.com |
| CAISO | ⚠️ Simulated | Requires registration | oasis.caiso.com |
| MISO | ⚠️ Simulated | Requires API key | N/A |

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Optional - for EIA data
EIA_API_KEY=your_api_key_here
```

### Settings
- Cache directory: `data/cache/`
- Default frequency: Hourly
- Timezone: UTC (converted from local)

## 📈 Sample Usage Scenarios

### Scenario 1: Get Latest Prices
```python
loader = DataLoader()
df = loader.load_iso_data(iso='ERCOT')
latest_price = df.iloc[-1]['price_per_mwh']
print(f"Latest Texas electricity price: ${latest_price:.2f}/MWh")
```

### Scenario 2: Historical Analysis
```python
from datetime import datetime, timedelta

# Get last 30 days of sample data
df = loader.load_sample_data(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    frequency='h'
)
```

### Scenario 3: Compare Markets
```python
# Load all real market data
df = loader.load_iso_data(iso='all', include_simulated=False)

# Group by ISO and calculate statistics
stats = df.groupby('iso')['price_per_mwh'].agg(['mean', 'std', 'min', 'max'])
print(stats)
```

## 🐛 Troubleshooting

### Issue: ModuleNotFoundError
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: No data returned
```python
# Check internet connection
# Try sample data first
df = loader.load_sample_data()
print(f"Sample data works: {not df.empty}")
```

### Issue: Timezone errors
```python
# Data is automatically converted to timezone-naive
# All timestamps are in UTC
```

## 📊 Data Format

All data sources return a standardized DataFrame:
```
timestamp         | price_per_mwh | zone    | iso
------------------|---------------|---------|-------
2024-01-01 00:00  | 35.50        | NYC     | NYISO
2024-01-01 01:00  | 38.25        | NYC     | NYISO
```

## 🚦 Performance

- **NYISO**: ~270 records (5-minute intervals)
- **ERCOT**: ~7,500 records (real-time, aggregated to hourly)
- **Sample**: Configurable (default 168 hours/week)
- **Caching**: Automatic, 15-minute expiry
- **Load time**: <2 seconds for cached data

## 📝 Next Steps

1. **Add Forecasting Models**: Implement ARIMA and LSTM
2. **Create Dashboard**: Build Streamlit interface
3. **Add More ISOs**: SPP, ISO-NE integration
4. **Historical Data**: Add historical data retrieval
5. **Alerts**: Price spike notifications

## 📄 License

MIT License - See LICENSE file

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a pull request

## 📧 Support

For issues or questions:
- Create an issue on GitHub
- Check `DATA_SOURCES.md` for detailed API information
- Review `CLAUDE.md` for development guidelines

---

**Ready to start?** Run `python main.py` and select option 1 for a quick demo!