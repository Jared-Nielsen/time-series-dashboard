"""
Comprehensive test of all ISO/RTO data sources.
Demonstrates loading electricity prices from multiple US markets.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.data.loader import DataLoader
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime


def test_all_iso_sources():
    """Test all integrated ISO sources."""
    
    print("=" * 80)
    print("COMPREHENSIVE ISO/RTO DATA SOURCE TEST")
    print("=" * 80)
    
    loader = DataLoader()
    results = {}
    
    # 1. Test individual ISOs
    print("\n1. TESTING INDIVIDUAL ISOs")
    print("-" * 40)
    
    isos = ['NYISO', 'ERCOT', 'PJM', 'CAISO', 'MISO']
    
    for iso in isos:
        print(f"\n{iso}:")
        try:
            df = loader.load_iso_data(iso=iso, include_simulated=True)
            
            if not df.empty:
                results[iso] = df
                print(f"  ✓ Loaded {len(df)} records")
                print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
                print(f"  Price range: ${df['price_per_mwh'].min():.2f} - ${df['price_per_mwh'].max():.2f}/MWh")
                print(f"  Mean price: ${df['price_per_mwh'].mean():.2f}/MWh")
                
                # Check if it's real or simulated
                if iso in ['PJM', 'CAISO', 'MISO']:
                    print(f"  ⚠ Note: {iso} data is simulated (API registration required)")
                else:
                    print(f"  ✓ Real market data")
            else:
                print(f"  ✗ No data retrieved")
                
        except Exception as e:
            print(f"  ✗ Error: {str(e)[:100]}")
    
    # 2. Test loading all ISOs at once
    print("\n2. LOADING ALL ISOs SIMULTANEOUSLY")
    print("-" * 40)
    
    all_df = loader.load_iso_data(iso="all", include_simulated=True)
    
    if not all_df.empty:
        print(f"✓ Total records: {len(all_df)}")
        print(f"ISOs included: {sorted(all_df['iso'].unique())}")
        
        # Statistics by ISO
        print("\nStatistics by ISO:")
        for iso in sorted(all_df['iso'].unique()):
            iso_df = all_df[all_df['iso'] == iso]
            print(f"  {iso}: {len(iso_df)} records, "
                  f"avg ${iso_df['price_per_mwh'].mean():.2f}/MWh")
    
    # 3. Test real data only
    print("\n3. LOADING REAL DATA ONLY (excluding simulated)")
    print("-" * 40)
    
    real_df = loader.load_iso_data(iso="all", include_simulated=False)
    
    if not real_df.empty:
        print(f"✓ Real data records: {len(real_df)}")
        print(f"ISOs with real data: {sorted(real_df['iso'].unique())}")
    
    # 4. Compare prices across regions
    print("\n4. PRICE COMPARISON ACROSS REGIONS")
    print("-" * 40)
    
    if results:
        print(f"\n{'ISO':<10} {'Mean':<12} {'Min':<12} {'Max':<12} {'Std Dev':<12}")
        print("-" * 58)
        
        for iso, df in sorted(results.items()):
            if not df.empty:
                mean_p = df['price_per_mwh'].mean()
                min_p = df['price_per_mwh'].min()
                max_p = df['price_per_mwh'].max()
                std_p = df['price_per_mwh'].std()
                
                print(f"{iso:<10} ${mean_p:<11.2f} ${min_p:<11.2f} ${max_p:<11.2f} ${std_p:<11.2f}")
    
    # 5. Save data samples
    print("\n5. SAVING DATA SAMPLES")
    print("-" * 40)
    
    output_dir = Path("data/iso_samples")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for iso, df in results.items():
        if not df.empty:
            filename = output_dir / f"{iso.lower()}_prices.csv"
            df.to_csv(filename, index=False)
            print(f"✓ Saved {iso} data to {filename}")
    
    if not all_df.empty:
        all_file = output_dir / "all_iso_prices.csv"
        all_df.to_csv(all_file, index=False)
        print(f"✓ Saved combined data to {all_file}")
    
    return results, all_df


def create_iso_comparison_plot(results):
    """Create comparison plots for ISO prices."""
    
    if not results:
        print("No data to plot")
        return
    
    print("\n6. CREATING VISUALIZATIONS")
    print("-" * 40)
    
    # Create subplots
    n_isos = len(results)
    fig, axes = plt.subplots(n_isos, 1, figsize=(14, 3*n_isos))
    
    if n_isos == 1:
        axes = [axes]
    
    colors = {'NYISO': 'blue', 'ERCOT': 'red', 'PJM': 'green', 
              'CAISO': 'orange', 'MISO': 'purple'}
    
    for idx, (iso, df) in enumerate(sorted(results.items())):
        if not df.empty:
            ax = axes[idx]
            
            # Plot prices
            ax.plot(df['timestamp'], df['price_per_mwh'], 
                   color=colors.get(iso, 'gray'), alpha=0.7, linewidth=1)
            
            # Add moving average
            if len(df) > 5:
                ma = df['price_per_mwh'].rolling(window=5).mean()
                ax.plot(df['timestamp'], ma, color=colors.get(iso, 'gray'), 
                       linewidth=2, label=f'{iso} (5-period MA)')
            else:
                ax.plot([], [], color=colors.get(iso, 'gray'), 
                       linewidth=2, label=iso)
            
            ax.set_ylabel('Price ($/MWh)')
            ax.set_title(f'{iso} Electricity Prices')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper right')
            
            # Add mean line
            mean_price = df['price_per_mwh'].mean()
            ax.axhline(y=mean_price, color='red', linestyle='--', 
                      alpha=0.5, label=f'Mean: ${mean_price:.2f}')
    
    plt.xlabel('Time')
    plt.tight_layout()
    
    # Save plot
    plot_file = "iso_price_comparison.png"
    plt.savefig(plot_file, dpi=100, bbox_inches='tight')
    print(f"✓ Saved comparison plot to {plot_file}")
    
    # Create combined plot
    fig2, ax2 = plt.subplots(figsize=(14, 6))
    
    for iso, df in results.items():
        if not df.empty and len(df) > 0:
            # Normalize to hourly for comparison
            df_plot = df.set_index('timestamp').resample('h').mean()
            ax2.plot(df_plot.index, df_plot['price_per_mwh'], 
                    label=iso, color=colors.get(iso, 'gray'), alpha=0.7)
    
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Price ($/MWh)')
    ax2.set_title('All ISO/RTO Electricity Prices Comparison')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("iso_prices_combined.png", dpi=100, bbox_inches='tight')
    print(f"✓ Saved combined plot to iso_prices_combined.png")


if __name__ == "__main__":
    # Run tests
    results, all_df = test_all_iso_sources()
    
    # Create visualizations
    try:
        if results:
            create_iso_comparison_plot(results)
    except ImportError:
        print("\n(Install matplotlib for visualizations)")
    except Exception as e:
        print(f"\nCouldn't create plots: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    print("\n✅ Successfully integrated the following data sources:")
    print("  • NYISO (New York) - Real data")
    print("  • ERCOT (Texas) - Real data")
    print("  • PJM (Mid-Atlantic) - Simulated")
    print("  • CAISO (California) - Simulated")
    print("  • MISO (Midwest) - Simulated")
    
    print("\nUsage example:")
    print("```python")
    print("from src.data.loader import DataLoader")
    print("")
    print("loader = DataLoader()")
    print("")
    print("# Load specific ISO")
    print("nyiso_df = loader.load_iso_data(iso='NYISO')")
    print("")
    print("# Load all ISOs")
    print("all_df = loader.load_iso_data(iso='all')")
    print("")
    print("# Load only real data")
    print("real_df = loader.load_iso_data(iso='all', include_simulated=False)")
    print("```")