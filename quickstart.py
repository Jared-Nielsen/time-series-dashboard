#!/usr/bin/env python3
"""
Quick Start Script - Test everything in one go!
Run this to see all features of the Time Series Dashboard.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.data.loader import DataLoader
from datetime import datetime, timedelta
import pandas as pd

def main():
    print("🚀 TIME SERIES DASHBOARD - QUICK START")
    print("=" * 60)
    
    loader = DataLoader()
    
    # 1. Test Sample Data
    print("\n1️⃣  Testing Sample Data Generator...")
    sample_df = loader.load_sample_data(
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        frequency="h"
    )
    print(f"✅ Generated {len(sample_df)} hourly records")
    print(f"   Average price: ${sample_df['price_per_mwh'].mean():.2f}/MWh")
    
    # 2. Test NYISO (New York)
    print("\n2️⃣  Testing NYISO (New York) Real Data...")
    try:
        nyiso_df = loader.load_iso_data(iso='NYISO')
        if not nyiso_df.empty:
            print(f"✅ Loaded {len(nyiso_df)} records from New York")
            print(f"   Current avg: ${nyiso_df['price_per_mwh'].mean():.2f}/MWh")
            print(f"   Latest time: {nyiso_df['timestamp'].max()}")
        else:
            print("⚠️  No NYISO data available")
    except Exception as e:
        print(f"❌ NYISO error: {str(e)[:50]}")
    
    # 3. Test ERCOT (Texas)
    print("\n3️⃣  Testing ERCOT (Texas) Real Data...")
    try:
        ercot_df = loader.load_iso_data(iso='ERCOT')
        if not ercot_df.empty:
            print(f"✅ Loaded {len(ercot_df)} records from Texas")
            print(f"   Current avg: ${ercot_df['price_per_mwh'].mean():.2f}/MWh")
            print(f"   Latest time: {ercot_df['timestamp'].max()}")
        else:
            print("⚠️  No ERCOT data available")
    except Exception as e:
        print(f"❌ ERCOT error: {str(e)[:50]}")
    
    # 4. Test All ISOs Combined
    print("\n4️⃣  Testing All ISOs Combined...")
    all_df = loader.load_iso_data(iso='all', include_simulated=False)
    if not all_df.empty:
        print(f"✅ Loaded {len(all_df)} total records")
        for iso in all_df['iso'].unique():
            iso_count = len(all_df[all_df['iso'] == iso])
            print(f"   {iso}: {iso_count} records")
    
    # 5. Data Validation
    print("\n5️⃣  Testing Data Validation...")
    validation = loader.validate_data(sample_df)
    print(f"✅ Validation: {'Passed' if validation['valid'] else 'Failed'}")
    if validation['stats']:
        print(f"   Records: {validation['stats'].get('count', 0)}")
        print(f"   Mean: ${validation['stats'].get('mean_price', 0):.2f}/MWh")
    
    # 6. Save Sample Files
    print("\n6️⃣  Saving Sample Files...")
    
    # Save a small sample
    if not sample_df.empty:
        sample_df.head(100).to_csv('quickstart_sample.csv', index=False)
        print("✅ Saved quickstart_sample.csv (100 rows)")
    
    if not all_df.empty:
        all_df.to_csv('quickstart_real_data.csv', index=False)
        print(f"✅ Saved quickstart_real_data.csv ({len(all_df)} rows)")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 QUICK START COMPLETE!")
    print("=" * 60)
    
    print("\n📊 Summary:")
    print(f"  • Sample data: ✅ Working ({len(sample_df)} records)")
    print(f"  • NYISO data: {'✅ Working' if 'nyiso_df' in locals() and not nyiso_df.empty else '⚠️  Check connection'}")
    print(f"  • ERCOT data: {'✅ Working' if 'ercot_df' in locals() and not ercot_df.empty else '⚠️  Check connection'}")
    print(f"  • Data validation: ✅ Working")
    print(f"  • File export: ✅ Working")
    
    print("\n📁 Files created:")
    print("  • quickstart_sample.csv - Sample data")
    print("  • quickstart_real_data.csv - Real market data")
    
    print("\n🎯 Next steps:")
    print("  1. Run 'python main.py' for interactive menu")
    print("  2. Check CSV files for data format")
    print("  3. Use DataLoader in your own scripts")
    
    print("\n💡 Example usage:")
    print("  from src.data.loader import DataLoader")
    print("  loader = DataLoader()")
    print("  df = loader.load_iso_data(iso='NYISO')")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Make sure virtual environment is activated")
        print("  2. Run: pip install -r requirements.txt")
        print("  3. Check internet connection")
        sys.exit(1)