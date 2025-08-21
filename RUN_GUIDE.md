# 🚀 Complete Guide: How to Run and Test the Time Series Dashboard

## Prerequisites

1. **Python 3.8+** installed
2. **pip** package manager
3. **Internet connection** (for real-time data)

## Step-by-Step Setup

### 1️⃣ Initial Setup (One Time Only)

```bash
# Navigate to project directory
cd time-series-dashboard

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Quick Test - Verify Everything Works

```bash
# Run the quick start script
python quickstart.py
```

**Expected Output:**
- ✅ Sample data generator works
- ✅ NYISO (New York) data loads
- ✅ ERCOT (Texas) data loads
- ✅ Files created: `quickstart_sample.csv`, `quickstart_real_data.csv`

## 📊 Different Ways to Run

### Option A: Interactive Menu (Recommended for First Time)

```bash
python main.py
```

**Menu Options:**
1. **Quick Demo** - See all data sources at once
2. **Load Real Market Data** - Get NYISO + ERCOT prices
3. **Load Specific ISO** - Choose individual market
4. **Generate Sample Data** - Create test data
5. **Test Data Validation** - Check data quality
6. **View Statistics** - Compare all sources
7. **Export Data** - Save for analysis
8. **Exit** - Quit application

### Option B: Python Script

Create a file `my_test.py`:

```python
from src.data.loader import DataLoader

# Initialize loader
loader = DataLoader()

# Get real-time Texas electricity prices
ercot_data = loader.load_iso_data(iso='ERCOT')
print(f"Texas: {len(ercot_data)} records")
print(f"Latest price: ${ercot_data.iloc[-1]['price_per_mwh']:.2f}/MWh")

# Get New York prices
nyiso_data = loader.load_iso_data(iso='NYISO')
print(f"New York: {len(nyiso_data)} records")
print(f"Average price: ${nyiso_data['price_per_mwh'].mean():.2f}/MWh")

# Save to CSV
ercot_data.to_csv('texas_prices.csv', index=False)
nyiso_data.to_csv('ny_prices.csv', index=False)
```

Run it:
```bash
python my_test.py
```

### Option C: Jupyter Notebook

```python
# In a Jupyter cell
from src.data.loader import DataLoader
import pandas as pd
import matplotlib.pyplot as plt

loader = DataLoader()

# Load all real data
df = loader.load_iso_data(iso='all', include_simulated=False)

# Group by ISO
for iso in df['iso'].unique():
    iso_df = df[df['iso'] == iso]
    plt.figure(figsize=(12, 4))
    plt.plot(iso_df['timestamp'], iso_df['price_per_mwh'])
    plt.title(f'{iso} Electricity Prices')
    plt.xlabel('Time')
    plt.ylabel('Price ($/MWh)')
    plt.show()
```

### Option D: Command Line One-Liners

```bash
# Get current ERCOT price
python -c "from src.data.loader import DataLoader; l=DataLoader(); d=l.load_iso_data('ERCOT'); print(f'Current TX price: ${d.iloc[-1][\"price_per_mwh\"]:.2f}/MWh')"

# Get NYISO average
python -c "from src.data.loader import DataLoader; l=DataLoader(); d=l.load_iso_data('NYISO'); print(f'NY avg: ${d[\"price_per_mwh\"].mean():.2f}/MWh')"

# Generate week of sample data
python -c "from src.data.loader import DataLoader; l=DataLoader(); d=l.load_sample_data(); d.to_csv('week_sample.csv'); print(f'Saved {len(d)} rows')"
```

## 🧪 Testing Different Features

### Test 1: Real Market Data
```python
from src.data.loader import DataLoader

loader = DataLoader()
df = loader.load_iso_data(iso='all', include_simulated=False)

print(f"Total records: {len(df)}")
print(f"ISOs: {df['iso'].unique()}")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
```

### Test 2: Data Validation
```python
loader = DataLoader()
df = loader.load_sample_data()
validation = loader.validate_data(df)

print(f"Valid: {validation['valid']}")
print(f"Issues: {validation['issues']}")
print(f"Stats: {validation['stats']}")
```

### Test 3: Compare Markets
```python
loader = DataLoader()

# Load both markets
nyiso = loader.load_iso_data('NYISO')
ercot = loader.load_iso_data('ERCOT')

print(f"NYISO avg: ${nyiso['price_per_mwh'].mean():.2f}/MWh")
print(f"ERCOT avg: ${ercot['price_per_mwh'].mean():.2f}/MWh")
print(f"Difference: ${abs(nyiso['price_per_mwh'].mean() - ercot['price_per_mwh'].mean()):.2f}/MWh")
```

## 📁 Output Files

After running tests, check these files:

| File | Description | Size |
|------|-------------|------|
| `quickstart_sample.csv` | Sample data (100 rows) | ~10KB |
| `quickstart_real_data.csv` | Real market data | ~50KB |
| `real_iso_data.csv` | Combined ISO data | ~50KB |
| `data/cache/*.parquet` | Cached API responses | Various |
| `data/iso_samples/*.csv` | Individual ISO files | ~20KB each |

## 🔍 Verify Installation

Run this verification script:

```python
# verify.py
import sys
print("Python version:", sys.version)

try:
    import pandas
    print("✅ pandas installed:", pandas.__version__)
except:
    print("❌ pandas not installed")

try:
    import requests
    print("✅ requests installed:", requests.__version__)
except:
    print("❌ requests not installed")

try:
    from src.data.loader import DataLoader
    print("✅ DataLoader accessible")
    loader = DataLoader()
    df = loader.load_sample_data()
    print(f"✅ Sample data works: {len(df)} rows")
except Exception as e:
    print(f"❌ Error: {e}")
```

## 🐛 Troubleshooting

### Problem: `ModuleNotFoundError`
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows

# Reinstall requirements
pip install -r requirements.txt
```

### Problem: No internet connection
```python
# Use sample data instead
loader = DataLoader()
df = loader.load_sample_data()  # Works offline
```

### Problem: Timezone errors
```python
# Already fixed - all timestamps converted to UTC naive
```

### Problem: Can't find main.py
```bash
# Make sure you're in the right directory
ls -la  # Should see main.py, quickstart.py, etc.
pwd     # Should show .../time-series-dashboard
```

## 🎯 Quick Commands Reference

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python main.py          # Interactive menu
python quickstart.py    # Quick test
python test_iso_final.py # Test ISOs

# Python usage
from src.data.loader import DataLoader
loader = DataLoader()
df = loader.load_iso_data('NYISO')  # or 'ERCOT', 'all'
```

## ✅ Success Indicators

You know everything is working when:
1. `quickstart.py` shows all green checkmarks
2. Files are created in the directory
3. You see real timestamps (like "2025-08-20")
4. NYISO shows ~270 records
5. ERCOT shows ~21 hourly records
6. No red error messages

## 📞 Need Help?

1. Check `README.md` for overview
2. Check `DATA_SOURCES.md` for API details
3. Check `CLAUDE.md` for development info
4. Run `python quickstart.py` to test
5. Look at generated CSV files to see data format

---

**Ready to go?** Start with `python main.py` and select option 1!