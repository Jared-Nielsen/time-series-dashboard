"""
Demonstration of all available electricity price data sources.
Shows how to load data from each source for testing and development.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.data.loader import DataLoader
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt


def demo_all_sources():
    """Demonstrate all available data sources."""
    
    print("=" * 70)
    print("ELECTRICITY PRICE DATA SOURCES DEMONSTRATION")
    print("=" * 70)
    
    loader = DataLoader()
    all_data = {}
    
    # 1. Sample Data (Always available)
    print("\n1. SAMPLE DATA SOURCE")
    print("-" * 40)
    print("Generating synthetic electricity price data...")
    
    sample_df = loader.load_sample_data(
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        frequency="h"
    )
    
    if not sample_df.empty:
        all_data['Sample'] = sample_df
        print(f"✓ Generated {len(sample_df)} hourly records")
        print(f"  Date range: {sample_df['timestamp'].min()} to {sample_df['timestamp'].max()}")
        print(f"  Price range: ${sample_df['price_per_mwh'].min():.2f} - ${sample_df['price_per_mwh'].max():.2f}/MWh")
        print(f"  Mean price: ${sample_df['price_per_mwh'].mean():.2f}/MWh")
    
    # 2. ERCOT Live Data (Texas)
    print("\n2. ERCOT LIVE DATA (Texas)")
    print("-" * 40)
    print("Fetching real-time Texas electricity prices...")
    
    try:
        ercot_df = loader.load_ercot_data(aggregation="hourly")
        
        if not ercot_df.empty:
            all_data['ERCOT'] = ercot_df
            print(f"✓ Fetched {len(ercot_df)} hourly records")
            print(f"  Date range: {ercot_df['timestamp'].min()} to {ercot_df['timestamp'].max()}")
            print(f"  Price range: ${ercot_df['price_per_mwh'].min():.2f} - ${ercot_df['price_per_mwh'].max():.2f}/MWh")
            print(f"  Mean price: ${ercot_df['price_per_mwh'].mean():.2f}/MWh")
            print(f"  Latest price: ${ercot_df.iloc[-1]['price_per_mwh']:.2f}/MWh")
        else:
            print("✗ No ERCOT data available")
    except Exception as e:
        print(f"✗ Error loading ERCOT data: {e}")
    
    # 3. EIA Data (if configured)
    print("\n3. EIA DATA (U.S. Energy Information Administration)")
    print("-" * 40)
    print("Checking EIA API...")
    
    try:
        # Try to load a small sample
        eia_df = loader.load_eia_data(
            region="NYIS",
            start_date=datetime(2024, 12, 1),
            end_date=datetime(2024, 12, 2),
            use_cache=True
        )
        
        if not eia_df.empty:
            all_data['EIA'] = eia_df
            print(f"✓ EIA API configured and working")
            print(f"  Sample: {len(eia_df)} records from NYIS region")
        else:
            print("⚠ EIA API configured but no price data available")
            print("  (API provides demand/generation data only)")
    except Exception as e:
        print(f"⚠ EIA API not available: {str(e)[:100]}")
    
    # 4. CSV Upload capability
    print("\n4. CSV FILE UPLOAD")
    print("-" * 40)
    print("CSV upload capability is available")
    print("  Expected format: columns for timestamp and price")
    print("  Supported column names:")
    print("    - Time: 'timestamp', 'date', 'datetime', 'time'")
    print("    - Price: 'price', 'price_per_mwh', 'cost', 'lmp'")
    
    # Data Comparison
    if len(all_data) > 1:
        print("\n" + "=" * 70)
        print("DATA COMPARISON")
        print("=" * 70)
        
        print("\nSource Statistics:")
        print(f"{'Source':<15} {'Records':<10} {'Mean Price':<15} {'Std Dev':<15} {'Date Range'}")
        print("-" * 80)
        
        for name, df in all_data.items():
            if not df.empty:
                mean_price = df['price_per_mwh'].mean()
                std_price = df['price_per_mwh'].std()
                date_range = f"{df['timestamp'].min().strftime('%Y-%m-%d')} to {df['timestamp'].max().strftime('%Y-%m-%d')}"
                print(f"{name:<15} {len(df):<10} ${mean_price:<14.2f} ${std_price:<14.2f} {date_range}")
    
    # Save sample data for testing
    print("\n" + "=" * 70)
    print("SAVING SAMPLE DATA FILES")
    print("=" * 70)
    
    sample_dir = Path("data/samples")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    for name, df in all_data.items():
        if not df.empty:
            filename = sample_dir / f"{name.lower()}_sample.csv"
            df.to_csv(filename, index=False)
            print(f"✓ Saved {name} data to {filename}")
    
    return all_data


def plot_comparison(all_data):
    """Create a comparison plot of different data sources."""
    
    if not all_data:
        print("No data to plot")
        return
    
    print("\nCreating comparison plot...")
    
    fig, axes = plt.subplots(len(all_data), 1, figsize=(12, 4*len(all_data)), sharex=False)
    
    if len(all_data) == 1:
        axes = [axes]
    
    for idx, (name, df) in enumerate(all_data.items()):
        if not df.empty:
            ax = axes[idx]
            ax.plot(df['timestamp'], df['price_per_mwh'], label=name, alpha=0.7)
            ax.set_ylabel('Price ($/MWh)')
            ax.set_title(f'{name} Electricity Prices')
            ax.grid(True, alpha=0.3)
            ax.legend()
    
    plt.xlabel('Time')
    plt.tight_layout()
    
    plot_file = "data_sources_comparison.png"
    plt.savefig(plot_file, dpi=100, bbox_inches='tight')
    print(f"✓ Saved comparison plot to {plot_file}")
    
    return fig


if __name__ == "__main__":
    # Run the demonstration
    all_data = demo_all_sources()
    
    # Create visualization if matplotlib is available
    try:
        if all_data:
            plot_comparison(all_data)
    except ImportError:
        print("\n(Install matplotlib to see data visualizations)")
    except Exception as e:
        print(f"\nCouldn't create plot: {e}")
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nYou can now use any of these data sources in your dashboard:")
    print("  - Sample data for development and testing")
    print("  - ERCOT for real Texas electricity prices")
    print("  - CSV upload for your own data")
    print("\nNext steps:")
    print("  1. Choose your data source")
    print("  2. Load the data using DataLoader")
    print("  3. Build ARIMA and LSTM models")
    print("  4. Create the dashboard interface")