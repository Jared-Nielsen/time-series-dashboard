# Electricity Price Data Sources

## Overview
This document describes the available data sources for electricity price time series data in the dashboard application.

## 1. Sample Data Generator (Built-in)
**Status: ✅ Fully Functional**

The application includes a sophisticated sample data generator that creates realistic electricity price data with:
- Daily patterns (higher during peak hours)
- Weekly patterns (weekday vs weekend)
- Seasonal variations
- Random price spikes (simulating extreme weather events)
- Configurable frequency (hourly or daily)

**Usage:**
```python
from src.data.loader import DataLoader

loader = DataLoader()
df = loader.load_sample_data(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    frequency="h"  # hourly data
)
```

## 2. CSV File Upload
**Status: ✅ Fully Functional**

Users can upload their own electricity price data in CSV format.

**Required Format:**
- Must contain a timestamp/date column
- Must contain a price column
- Column names are flexible (auto-detected)

**Supported Column Names:**
- Time: 'timestamp', 'date', 'datetime', 'time'
- Price: 'price', 'price_per_mwh', 'cost', 'lmp'

**Usage:**
```python
loader = DataLoader()
df = loader.load_csv_data(file_path="path/to/your/data.csv")
```

## 3. EIA API (U.S. Energy Information Administration)
**Status: ⚠️ Limited - Demand/Generation Data Only**

The EIA API v2 provides electricity data but the wholesale price endpoints appear to be restructured or removed. Currently available data includes:
- Electricity demand (D)
- Day-ahead demand forecast (DF)
- Net generation (NG)
- Total interchange (TI)

**Note:** Direct wholesale electricity price data is not currently available through the tested endpoints. The API key is configured and working for other electricity metrics.

**Regions Supported:**
- NYIS (New York Independent System Operator)
- PJM (PJM Interconnection)
- CAISO (California ISO)
- ERCOT (Electric Reliability Council of Texas)
- MISO (Midcontinent ISO)

## 4. ERCOT Live Data (Texas)
**Status: ✅ Fully Functional**

Real-time electricity prices from the Texas grid (ERCOT - Electric Reliability Council of Texas).

**Features:**
- Real-time price updates (every few seconds)
- No authentication required
- Historical data for current day
- Hourly aggregation available

**Usage:**
```python
from src.data.loader import DataLoader

loader = DataLoader()

# Get raw real-time data (updates every few seconds)
df = loader.load_ercot_data(aggregation="raw")

# Get hourly aggregated data
df = loader.load_ercot_data(aggregation="hourly")
```

**Data Coverage:**
- Region: Texas (ERCOT grid)
- Frequency: Real-time (seconds) or hourly averages
- Availability: Current day's data
- Price Unit: $/MWh

## 5. Alternative Free Data Sources (Future Implementation)

### Recommended Sources for Real Price Data:

1. **NYISO (New York ISO)**
   - Website: https://www.nyiso.com/energy-market-operational-data
   - Provides: Real-time and day-ahead market prices
   - Format: CSV downloads
   - Update: Daily

2. **PJM Data Miner 2**
   - Website: https://dataminer2.pjm.com/
   - Provides: LMP (Locational Marginal Prices)
   - Format: CSV/Excel
   - Registration: Free but required

3. **CAISO OASIS**
   - Website: http://oasis.caiso.com/
   - Provides: California electricity prices
   - Format: CSV/XML
   - Access: Public

4. **ERCOT (Texas)**
   - Website: http://www.ercot.com/gridinfo/dashboards
   - Provides: Real-time and day-ahead prices
   - Format: Excel/CSV
   - Access: Public

## 6. All US ISOs/RTOs
**Status: ✅ Integrated**

Unified access to electricity prices from major US markets.

### Real Data (No Auth Required):
- **NYISO** (New York) - ✅ Working
- **ERCOT** (Texas) - ✅ Working

### Simulated Data (API Registration Required):
- **PJM** (Mid-Atlantic) - Requires registration at dataminer2.pjm.com
- **CAISO** (California) - Requires registration at oasis.caiso.com
- **MISO** (Midwest) - Requires API access

**Usage:**
```python
from src.data.loader import DataLoader

loader = DataLoader()

# Load specific ISO
nyiso_df = loader.load_iso_data(iso='NYISO')
ercot_df = loader.load_iso_data(iso='ERCOT')

# Load all ISOs (real + simulated)
all_df = loader.load_iso_data(iso='all', include_simulated=True)

# Load only real data
real_df = loader.load_iso_data(iso='all', include_simulated=False)
```

## Quick Start

For immediate testing and development, use the real ISO data or sample generator:

```python
from src.data.loader import quick_load

# Generate one year of hourly electricity price data
df = quick_load(source="sample")

# Or load your own CSV
df = quick_load(source="csv", file_path="your_data.csv")
```

## Data Validation

All data sources are validated for:
- Required columns (timestamp, price)
- Data types (datetime, numeric)
- Missing values
- Negative prices (flagged but allowed)

```python
loader = DataLoader()
df = loader.load_sample_data()
validation = loader.validate_data(df)
print(f"Data valid: {validation['valid']}")
print(f"Statistics: {validation['stats']}")
```

## Caching

Downloaded data is automatically cached in `data/cache/` to improve performance and reduce API calls.

## Environment Variables

Required for external APIs:
```bash
# .env file
EIA_API_KEY=your_eia_api_key_here
```

## Next Steps

1. For production use, implement direct connections to ISO/RTO websites for real price data
2. Consider adding support for European markets (ENTSO-E)
3. Implement automated data refresh schedules
4. Add data quality monitoring and alerting