"""
Test script for ERCOT data access.
Tries multiple methods to fetch Texas electricity prices.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import requests
from datetime import datetime, timedelta
import pandas as pd
import io


def test_ercot_direct_download():
    """Test direct download from ERCOT's public files."""
    print("\n" + "="*60)
    print("Testing Direct ERCOT File Download")
    print("="*60)
    
    # ERCOT posts daily reports at specific URLs
    # Try multiple date formats and URLs
    
    test_dates = [
        datetime.now() - timedelta(days=1),
        datetime.now() - timedelta(days=2),
        datetime.now() - timedelta(days=7),
    ]
    
    for test_date in test_dates:
        date_str = test_date.strftime("%m%d%Y")
        date_str2 = test_date.strftime("%Y%m%d")
        
        urls_to_try = [
            # MIS Public Reports format
            f"https://www.ercot.com/content/cdr/html/{date_str2}_dam_spp.html",
            f"https://www.ercot.com/misapp/GetReports.do?reportTypeId=13060&reportTitle=DAM%20Settlement%20Point%20Prices&showHTMLView=&mimicKey",
            
            # Direct CSV/Excel downloads
            f"https://www.ercot.com/content/cdr/html/{date_str}_dam_spp.html",
            f"http://mis.ercot.com/misapp/GetReports.do?reportTypeId=12331&reportTitle=DAM%20Settlement%20Point%20Prices",
        ]
        
        print(f"\nTrying date: {test_date.strftime('%Y-%m-%d')}")
        
        for url in urls_to_try:
            try:
                print(f"  Trying: {url[:70]}...")
                response = requests.get(url, timeout=10, allow_redirects=True)
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    print(f"    ✓ Success! Status: {response.status_code}, Type: {content_type}")
                    print(f"    Content length: {len(response.content)} bytes")
                    
                    # Check if it's CSV or HTML with data
                    if 'csv' in content_type.lower() or 'text' in content_type.lower():
                        print("    Attempting to parse as CSV...")
                        try:
                            df = pd.read_csv(io.StringIO(response.text))
                            print(f"    ✓ Parsed {len(df)} rows, {len(df.columns)} columns")
                            print(f"    Columns: {', '.join(df.columns[:5])}")
                            return df
                        except Exception as e:
                            print(f"    ✗ Parse error: {e}")
                    
                    # Save sample for inspection
                    sample_file = f"ercot_sample_{test_date.strftime('%Y%m%d')}.html"
                    with open(sample_file, 'w') as f:
                        f.write(response.text[:5000])
                    print(f"    Saved sample to {sample_file}")
                    
                else:
                    print(f"    ✗ Status: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"    ✗ Timeout")
            except Exception as e:
                print(f"    ✗ Error: {str(e)[:50]}")
    
    return None


def test_ercot_api_endpoints():
    """Test ERCOT API endpoints."""
    print("\n" + "="*60)
    print("Testing ERCOT API Endpoints")
    print("="*60)
    
    # Known ERCOT API endpoints
    endpoints = [
        "https://www.ercot.com/api/1/services/read/dashboards/daily-prc.json",
        "https://www.ercot.com/content/cdr/contours/rtmLmp.json",
        "https://www.ercot.com/api/1/services/read/dashboards/supply-demand.json",
        "https://www.ercot.com/api/1/services/read/dashboards/todays-outlook.json",
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\nTesting: {endpoint}")
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✓ Success! Status: {response.status_code}")
                
                try:
                    data = response.json()
                    print(f"  ✓ Valid JSON response")
                    
                    # Explore the structure
                    if isinstance(data, dict):
                        print(f"  Keys: {', '.join(list(data.keys())[:5])}")
                        
                        # Look for price data
                        for key in data.keys():
                            if 'price' in key.lower() or 'lmp' in key.lower():
                                print(f"  Found price data in key: {key}")
                                
                except Exception as e:
                    print(f"  ✗ JSON parse error: {e}")
                    
            else:
                print(f"  ✗ Status: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Error: {str(e)[:50]}")
    
    return None


def test_ercot_dashboard_api():
    """Test ERCOT's dashboard data API."""
    print("\n" + "="*60)
    print("Testing ERCOT Dashboard API")
    print("="*60)
    
    # ERCOT provides real-time data through their dashboard
    url = "https://www.ercot.com/api/1/services/read/dashboards/daily-prc.json"
    
    try:
        print(f"Fetching daily price data from ERCOT dashboard...")
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Successfully fetched dashboard data")
            
            # Parse the dashboard data
            if 'current' in data:
                current = data['current']
                print(f"\nCurrent Data:")
                for key, value in current.items():
                    if 'price' in key.lower() or 'lmp' in key.lower():
                        print(f"  {key}: {value}")
            
            if 'data' in data:
                df = pd.DataFrame(data['data'])
                print(f"\n✓ Converted to DataFrame: {len(df)} rows")
                print(f"Columns: {', '.join(df.columns)}")
                
                # Save sample
                df.to_csv("ercot_dashboard_sample.csv", index=False)
                print("Saved sample to ercot_dashboard_sample.csv")
                
                return df
                
        else:
            print(f"✗ Failed: Status {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    return None


def fetch_ercot_from_gridstatus():
    """
    Alternative: Use GridStatus.io API which aggregates ISO data.
    This is a third-party service that provides cleaned ERCOT data.
    """
    print("\n" + "="*60)
    print("Testing GridStatus.io API (Alternative Source)")
    print("="*60)
    
    # GridStatus.io provides free tier access to ISO data
    base_url = "https://api.gridstatus.io/v1/datasets"
    
    try:
        # Get ERCOT LMP data
        print("Fetching ERCOT data from GridStatus.io...")
        
        # Note: GridStatus requires registration for API key
        # For demo, we'll show the structure
        headers = {
            "User-Agent": "TimeSeriesDashboard/1.0"
        }
        
        # Check if service is accessible
        response = requests.get(
            f"{base_url}?iso=ercot&dataset=lmp_real_time",
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ GridStatus.io is accessible")
            print("Note: Full data access requires free API key from https://www.gridstatus.io/")
        elif response.status_code == 401:
            print("✓ GridStatus.io endpoint found (requires API key)")
            print("Sign up for free at: https://www.gridstatus.io/")
        else:
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    return None


if __name__ == "__main__":
    print("ERCOT Data Access Testing")
    print("=" * 60)
    
    # Test different access methods
    results = {}
    
    # 1. Test direct file download
    df1 = test_ercot_direct_download()
    results['direct'] = df1 is not None
    
    # 2. Test API endpoints
    df2 = test_ercot_api_endpoints()
    results['api'] = df2 is not None
    
    # 3. Test dashboard API
    df3 = test_ercot_dashboard_api()
    results['dashboard'] = df3 is not None
    
    # 4. Test alternative source
    df4 = fetch_ercot_from_gridstatus()
    results['gridstatus'] = df4 is not None
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for method, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {method.capitalize()}: {'Success' if success else 'Failed'}")
    
    print("\nRecommendations:")
    print("1. ERCOT data requires navigating their MIS portal")
    print("2. Consider using GridStatus.io API (free tier available)")
    print("3. Manual CSV download from ERCOT website is most reliable")
    print("4. For production, implement web scraping with proper delays")