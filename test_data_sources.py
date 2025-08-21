"""
Test script for electricity price data sources.
Run this to verify data sources are working correctly.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from datetime import datetime, timedelta
from src.data.loader import DataLoader
from src.data.sources import get_data_source
import pandas as pd


def test_sample_data():
    """Test sample data generation."""
    print("\n" + "="*60)
    print("Testing Sample Data Source")
    print("="*60)
    
    loader = DataLoader()
    df = loader.load_sample_data(
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now(),
        frequency="h"
    )
    
    print(f"Loaded {len(df)} rows of sample data")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Price statistics:")
    print(f"  Mean: ${df['price_per_mwh'].mean():.2f}/MWh")
    print(f"  Min:  ${df['price_per_mwh'].min():.2f}/MWh")
    print(f"  Max:  ${df['price_per_mwh'].max():.2f}/MWh")
    print("\nFirst 5 rows:")
    print(df.head())
    
    # Validate data
    validation = loader.validate_data(df)
    print(f"\nValidation: {'✓ Passed' if validation['valid'] else '✗ Failed'}")
    if validation['issues']:
        print("Issues found:", validation['issues'])
    
    return df


def test_eia_data():
    """Test EIA API data source."""
    print("\n" + "="*60)
    print("Testing EIA API Data Source")
    print("="*60)
    
    try:
        loader = DataLoader()
        
        # Test with recent historical data (EIA may not have 2025 data yet)
        # Using a date range from 2024 that should have data available
        end_date = datetime(2024, 12, 15)  # Mid-December 2024
        start_date = end_date - timedelta(days=7)
        
        print(f"Fetching NYIS (New York) electricity prices...")
        print(f"Date range: {start_date.date()} to {end_date.date()}")
        
        df = loader.load_eia_data(
            region="NYIS",
            start_date=start_date,
            end_date=end_date,
            use_cache=True
        )
        
        if len(df) > 0:
            print(f"\n✓ Successfully loaded {len(df)} rows from EIA API")
            print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"Price statistics:")
            print(f"  Mean: ${df['price_per_mwh'].mean():.2f}/MWh")
            print(f"  Min:  ${df['price_per_mwh'].min():.2f}/MWh")
            print(f"  Max:  ${df['price_per_mwh'].max():.2f}/MWh")
            print("\nLast 5 rows:")
            print(df.tail())
        else:
            print("⚠ No data returned from EIA API")
            
        # Validate data
        validation = loader.validate_data(df)
        print(f"\nValidation: {'✓ Passed' if validation['valid'] else '✗ Failed'}")
        if validation['issues']:
            print("Issues found:", validation['issues'])
            
        return df
        
    except Exception as e:
        print(f"✗ Error testing EIA API: {e}")
        print("\nTroubleshooting:")
        print("1. Check that your EIA_API_KEY is set in .env file")
        print("2. Verify internet connection")
        print("3. Check if the API endpoint is accessible")
        return None


def test_regions():
    """Test different EIA regions."""
    print("\n" + "="*60)
    print("Testing Different EIA Regions")
    print("="*60)
    
    regions = ["NYIS", "PJM", "CAISO", "ERCOT", "MISO"]
    loader = DataLoader()
    
    for region in regions:
        try:
            print(f"\nTesting {region}...", end=" ")
            df = loader.load_eia_data(
                region=region,
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
                use_cache=False
            )
            if len(df) > 0:
                print(f"✓ {len(df)} rows, avg price: ${df['price_per_mwh'].mean():.2f}/MWh")
            else:
                print("⚠ No data")
        except Exception as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("Time Series Dashboard - Data Source Testing")
    print("=" * 60)
    
    # Test sample data
    sample_df = test_sample_data()
    
    # Test EIA API
    eia_df = test_eia_data()
    
    # Test different regions (optional - comment out if you want faster testing)
    # test_regions()
    
    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)
    
    if eia_df is not None:
        print("\n✓ EIA API is working correctly with your API key")
        print("✓ Data can be loaded and cached successfully")
    else:
        print("\n⚠ EIA API test failed - check the error messages above")