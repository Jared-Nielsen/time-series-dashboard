#!/usr/bin/env python3
"""
Time Series Dashboard - Main Application
Run this file to test all data sources and see the application in action.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.data.loader import DataLoader


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)


def print_section(text):
    """Print formatted section."""
    print(f"\n{text}")
    print("-" * len(text))


def main():
    """Main application entry point."""
    
    print_header("TIME SERIES DASHBOARD - ELECTRICITY PRICE FORECASTING")
    print("\nWelcome to the Time Series Dashboard!")
    print("This application provides electricity price data for forecasting.\n")
    
    # Initialize data loader
    loader = DataLoader()
    
    while True:
        print("\n" + "=" * 70)
        print("MAIN MENU")
        print("=" * 70)
        print("\n1. Quick Demo - See all data sources")
        print("2. Load Real Market Data (NYISO + ERCOT)")
        print("3. Load Specific ISO Data")
        print("4. Generate Sample Data")
        print("5. Test Data Validation")
        print("6. View Data Statistics")
        print("7. Export Data for Analysis")
        print("8. Exit")
        
        choice = input("\nSelect an option (1-8): ").strip()
        
        if choice == "1":
            run_quick_demo(loader)
        elif choice == "2":
            load_real_data(loader)
        elif choice == "3":
            load_specific_iso(loader)
        elif choice == "4":
            generate_sample_data(loader)
        elif choice == "5":
            test_validation(loader)
        elif choice == "6":
            view_statistics(loader)
        elif choice == "7":
            export_data(loader)
        elif choice == "8":
            print("\nThank you for using Time Series Dashboard!")
            print("Goodbye!")
            break
        else:
            print("\n⚠ Invalid option. Please try again.")


def run_quick_demo(loader):
    """Run a quick demonstration of all data sources."""
    print_header("QUICK DEMO - ALL DATA SOURCES")
    
    print("\n📊 Available Data Sources:")
    print("  • Sample Generator - Synthetic data for testing")
    print("  • NYISO - Real New York electricity prices")
    print("  • ERCOT - Real Texas electricity prices")
    print("  • PJM, CAISO, MISO - Simulated data (API registration required)")
    
    input("\nPress Enter to load data from all sources...")
    
    # Load sample data
    print_section("1. Sample Data Generator")
    sample_df = loader.load_sample_data(
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        frequency="h"
    )
    if not sample_df.empty:
        print(f"✓ Generated {len(sample_df)} hourly records")
        print(f"  Mean price: ${sample_df['price_per_mwh'].mean():.2f}/MWh")
    
    # Load NYISO data
    print_section("2. NYISO (New York)")
    try:
        nyiso_df = loader.load_nyiso_data()
        if not nyiso_df.empty:
            print(f"✓ Loaded {len(nyiso_df)} records")
            print(f"  Mean price: ${nyiso_df['price_per_mwh'].mean():.2f}/MWh")
            print(f"  Latest: {nyiso_df['timestamp'].max()}")
    except Exception as e:
        print(f"✗ Error: {str(e)[:100]}")
    
    # Load ERCOT data
    print_section("3. ERCOT (Texas)")
    try:
        ercot_df = loader.load_ercot_data(aggregation="hourly")
        if not ercot_df.empty:
            print(f"✓ Loaded {len(ercot_df)} hourly records")
            print(f"  Mean price: ${ercot_df['price_per_mwh'].mean():.2f}/MWh")
            print(f"  Latest: {ercot_df['timestamp'].max()}")
    except Exception as e:
        print(f"✗ Error: {str(e)[:100]}")
    
    print("\n✅ Demo complete! Use the menu to explore specific data sources.")


def load_real_data(loader):
    """Load real market data from NYISO and ERCOT."""
    print_header("LOADING REAL MARKET DATA")
    
    print("\nFetching real electricity prices from:")
    print("  • NYISO (New York Independent System Operator)")
    print("  • ERCOT (Electric Reliability Council of Texas)")
    
    df = loader.load_iso_data(iso="all", include_simulated=False)
    
    if not df.empty:
        print(f"\n✓ Successfully loaded {len(df)} records")
        
        # Show breakdown by ISO
        print("\nData Summary:")
        for iso in df['iso'].unique():
            iso_df = df[df['iso'] == iso]
            print(f"\n{iso}:")
            print(f"  Records: {len(iso_df)}")
            print(f"  Date range: {iso_df['timestamp'].min()} to {iso_df['timestamp'].max()}")
            print(f"  Price range: ${iso_df['price_per_mwh'].min():.2f} - ${iso_df['price_per_mwh'].max():.2f}/MWh")
            print(f"  Mean: ${iso_df['price_per_mwh'].mean():.2f}/MWh")
            print(f"  Std Dev: ${iso_df['price_per_mwh'].std():.2f}/MWh")
        
        # Save option
        save = input("\nSave this data to CSV? (y/n): ").strip().lower()
        if save == 'y':
            filename = f"real_market_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            print(f"✓ Saved to {filename}")
    else:
        print("✗ No data loaded")


def load_specific_iso(loader):
    """Load data from a specific ISO."""
    print_header("LOAD SPECIFIC ISO DATA")
    
    print("\nAvailable ISOs:")
    print("1. NYISO (New York) - Real data")
    print("2. ERCOT (Texas) - Real data")
    print("3. PJM (Mid-Atlantic) - Simulated")
    print("4. CAISO (California) - Simulated")
    print("5. MISO (Midwest) - Simulated")
    
    iso_map = {
        "1": "NYISO",
        "2": "ERCOT", 
        "3": "PJM",
        "4": "CAISO",
        "5": "MISO"
    }
    
    choice = input("\nSelect ISO (1-5): ").strip()
    
    if choice in iso_map:
        iso = iso_map[choice]
        print(f"\nLoading {iso} data...")
        
        df = loader.load_iso_data(iso=iso, include_simulated=True)
        
        if not df.empty:
            print(f"\n✓ Loaded {len(df)} records from {iso}")
            print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"Price range: ${df['price_per_mwh'].min():.2f} - ${df['price_per_mwh'].max():.2f}/MWh")
            print(f"Mean: ${df['price_per_mwh'].mean():.2f}/MWh")
            
            # Show sample
            print("\nFirst 5 records:")
            print(df.head())
            
            # Save option
            save = input(f"\nSave {iso} data to CSV? (y/n): ").strip().lower()
            if save == 'y':
                filename = f"{iso.lower()}_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df.to_csv(filename, index=False)
                print(f"✓ Saved to {filename}")
        else:
            print(f"✗ No data loaded from {iso}")
    else:
        print("⚠ Invalid selection")


def generate_sample_data(loader):
    """Generate sample data for testing."""
    print_header("GENERATE SAMPLE DATA")
    
    print("\nConfigure sample data generation:")
    
    # Get parameters
    days = input("Number of days of data (default 30): ").strip()
    days = int(days) if days else 30
    
    freq = input("Frequency - (h)ourly or (d)aily (default h): ").strip().lower()
    freq = freq if freq in ['h', 'd'] else 'h'
    
    print(f"\nGenerating {days} days of {'hourly' if freq == 'h' else 'daily'} data...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    df = loader.load_sample_data(
        start_date=start_date,
        end_date=end_date,
        frequency=freq
    )
    
    if not df.empty:
        print(f"\n✓ Generated {len(df)} records")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"Price range: ${df['price_per_mwh'].min():.2f} - ${df['price_per_mwh'].max():.2f}/MWh")
        print(f"Mean: ${df['price_per_mwh'].mean():.2f}/MWh")
        print(f"Std Dev: ${df['price_per_mwh'].std():.2f}/MWh")
        
        # Save
        filename = f"sample_data_{days}days_{freq}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n✓ Saved to {filename}")
    else:
        print("✗ Failed to generate data")


def test_validation(loader):
    """Test data validation functionality."""
    print_header("DATA VALIDATION TEST")
    
    print("\nLoading sample data for validation...")
    df = loader.load_sample_data(
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        frequency="h"
    )
    
    # Validate
    validation = loader.validate_data(df)
    
    print("\nValidation Results:")
    print(f"Valid: {'✓ Yes' if validation['valid'] else '✗ No'}")
    
    if validation['issues']:
        print("\nIssues found:")
        for issue in validation['issues']:
            print(f"  • {issue}")
    else:
        print("\n✓ No issues found")
    
    if validation['stats']:
        print("\nData Statistics:")
        for key, value in validation['stats'].items():
            if key == 'date_range' and value:
                print(f"  {key}: {value[0]} to {value[1]}")
            elif isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")


def view_statistics(loader):
    """View statistics for all data sources."""
    print_header("DATA SOURCE STATISTICS")
    
    print("\nGathering statistics from all sources...")
    
    sources = {
        'Sample': loader.load_sample_data(
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            frequency="h"
        ),
        'NYISO': loader.load_iso_data(iso='NYISO'),
        'ERCOT': loader.load_iso_data(iso='ERCOT')
    }
    
    print(f"\n{'Source':<10} {'Records':<10} {'Mean $/MWh':<12} {'Min $/MWh':<12} {'Max $/MWh':<12} {'Std Dev':<10}")
    print("-" * 70)
    
    for name, df in sources.items():
        if not df.empty and 'price_per_mwh' in df.columns:
            print(f"{name:<10} {len(df):<10} "
                  f"${df['price_per_mwh'].mean():<11.2f} "
                  f"${df['price_per_mwh'].min():<11.2f} "
                  f"${df['price_per_mwh'].max():<11.2f} "
                  f"${df['price_per_mwh'].std():<9.2f}")
        else:
            print(f"{name:<10} {'N/A':<10} {'N/A':<12} {'N/A':<12} {'N/A':<12} {'N/A':<10}")


def export_data(loader):
    """Export data for analysis."""
    print_header("EXPORT DATA FOR ANALYSIS")
    
    print("\nSelect data to export:")
    print("1. All real market data (NYISO + ERCOT)")
    print("2. Last 7 days sample data")
    print("3. Last 30 days sample data")
    print("4. Custom date range")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        df = loader.load_iso_data(iso="all", include_simulated=False)
        filename = "all_real_market_data.csv"
    elif choice == "2":
        df = loader.load_sample_data(
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            frequency="h"
        )
        filename = "sample_7days.csv"
    elif choice == "3":
        df = loader.load_sample_data(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            frequency="h"
        )
        filename = "sample_30days.csv"
    elif choice == "4":
        days = input("Enter number of days: ").strip()
        days = int(days) if days else 7
        df = loader.load_sample_data(
            start_date=datetime.now() - timedelta(days=days),
            end_date=datetime.now(),
            frequency="h"
        )
        filename = f"sample_{days}days.csv"
    else:
        print("⚠ Invalid selection")
        return
    
    if not df.empty:
        # Add timestamp for uniqueness
        filename = filename.replace('.csv', f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        df.to_csv(filename, index=False)
        print(f"\n✓ Exported {len(df)} records to {filename}")
        
        # Also create a Parquet file for faster loading
        parquet_file = filename.replace('.csv', '.parquet')
        df.to_parquet(parquet_file)
        print(f"✓ Also saved as {parquet_file} for faster loading")
    else:
        print("✗ No data to export")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nIf you encounter issues, please check:")
        print("  1. Virtual environment is activated")
        print("  2. Dependencies are installed (pip install -r requirements.txt)")
        print("  3. .env file exists with API keys (if using EIA)")
        sys.exit(1)