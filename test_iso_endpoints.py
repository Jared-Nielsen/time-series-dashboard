"""
Test and discover working ISO endpoints.
"""

import requests
import pandas as pd
import io
from datetime import datetime, timedelta


def test_pjm_endpoints():
    """Test various PJM data endpoints."""
    print("\n" + "="*60)
    print("Testing PJM Endpoints")
    print("="*60)
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    endpoints = [
        # PJM public data
        ("https://www.pjm.com/pub/pricing/rt-fivemin-lmp.csv", "RT 5-min LMP"),
        ("https://datasnapshot.pjm.com/content/InstantaneousLoad.csv", "Instantaneous Load"),
        ("https://datasnapshot.pjm.com/content/PricingData.csv", "Pricing Data"),
        ("https://api.pjm.com/api/v1/rt_fivemin_lmps", "API RT LMP"),
        ("https://www.pjm.com/pub/pricing/da_lmps.csv", "DA LMP"),
    ]
    
    for url, name in endpoints:
        try:
            print(f"\nTesting: {name}")
            print(f"URL: {url}")
            response = session.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                print(f"Content-Type: {content_type}")
                print(f"Size: {len(response.content)} bytes")
                
                # Try to parse as CSV
                if 'csv' in content_type.lower() or url.endswith('.csv'):
                    try:
                        df = pd.read_csv(io.StringIO(response.text))
                        print(f"✓ Parsed CSV: {len(df)} rows, {len(df.columns)} columns")
                        print(f"Columns: {', '.join(df.columns[:5])}")
                        
                        # Save sample
                        sample_file = f"pjm_sample_{name.replace(' ', '_').lower()}.csv"
                        df.head(10).to_csv(sample_file, index=False)
                        print(f"Saved sample to {sample_file}")
                        
                        return df
                    except Exception as e:
                        print(f"✗ Parse error: {str(e)[:100]}")
                        
        except requests.exceptions.Timeout:
            print(f"✗ Timeout")
        except Exception as e:
            print(f"✗ Error: {str(e)[:100]}")
    
    return None


def test_caiso_endpoints():
    """Test various CAISO data endpoints."""
    print("\n" + "="*60)
    print("Testing CAISO Endpoints")
    print("="*60)
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    endpoints = [
        # CAISO public data
        ("http://www.caiso.com/Documents/FlexRampRequirement.csv", "Flex Ramp"),
        ("http://www.caiso.com/outlook/SP/prices_DAM.csv", "Day-Ahead Prices"),
        ("http://www.caiso.com/outlook/SP/prices.csv", "Current Prices"),
        ("http://www.caiso.com/outlook/SP/History/" + yesterday.strftime("%Y%m%d") + "/prices.csv", "Historical Prices"),
        ("https://www.caiso.com/Documents/SystemDemandForecast.csv", "Demand Forecast"),
    ]
    
    for url, name in endpoints:
        try:
            print(f"\nTesting: {name}")
            print(f"URL: {url}")
            response = session.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                print(f"Content-Type: {content_type}")
                print(f"Size: {len(response.content)} bytes")
                
                # Try to parse as CSV
                try:
                    df = pd.read_csv(io.StringIO(response.text))
                    print(f"✓ Parsed CSV: {len(df)} rows, {len(df.columns)} columns")
                    print(f"Columns: {', '.join(df.columns[:5])}")
                    
                    # Save sample
                    sample_file = f"caiso_sample_{name.replace(' ', '_').lower()}.csv"
                    df.head(10).to_csv(sample_file, index=False)
                    print(f"Saved sample to {sample_file}")
                    
                    # Check for price columns
                    price_cols = [col for col in df.columns if 'price' in col.lower() or 'lmp' in col.lower()]
                    if price_cols:
                        print(f"Found price columns: {price_cols}")
                        return df
                        
                except Exception as e:
                    print(f"✗ Parse error: {str(e)[:100]}")
                    
        except requests.exceptions.Timeout:
            print(f"✗ Timeout")
        except Exception as e:
            print(f"✗ Error: {str(e)[:100]}")
    
    return None


def test_nyiso_details():
    """Test NYISO data in detail."""
    print("\n" + "="*60)
    print("NYISO Data Details")
    print("="*60)
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    today = datetime.now().strftime("%Y%m%d")
    url = f"http://mis.nyiso.com/public/csv/realtime/{today}realtime_zone.csv"
    
    try:
        print(f"Fetching: {url}")
        response = session.get(url, timeout=15)
        
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            print(f"✓ Successfully loaded {len(df)} rows")
            print(f"\nColumns: {list(df.columns)}")
            print(f"\nZones available: {df['Name'].unique()}")
            print(f"\nSample data:")
            print(df.head())
            
            # Calculate average prices by zone
            print(f"\nAverage prices by zone:")
            for zone in df['Name'].unique():
                zone_df = df[df['Name'] == zone]
                avg_price = zone_df['LBMP ($/MWH)'].mean()
                print(f"  {zone}: ${avg_price:.2f}/MWh")
            
            return df
    except Exception as e:
        print(f"✗ Error: {e}")
    
    return None


if __name__ == "__main__":
    print("ISO Endpoint Discovery")
    print("=" * 60)
    
    # Test NYISO details
    nyiso_df = test_nyiso_details()
    
    # Test PJM endpoints
    pjm_df = test_pjm_endpoints()
    
    # Test CAISO endpoints
    caiso_df = test_caiso_endpoints()
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    print("\nWorking endpoints:")
    if nyiso_df is not None:
        print("✓ NYISO: Real-time zone prices")
    if pjm_df is not None:
        print("✓ PJM: Found working endpoint")
    if caiso_df is not None:
        print("✓ CAISO: Found working endpoint")