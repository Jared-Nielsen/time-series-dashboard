"""
ISO/RTO electricity price data sources.
Implements data fetching for major US electricity markets:
- NYISO (New York)
- PJM (Mid-Atlantic)  
- CAISO (California)
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json
from pathlib import Path
import zipfile
import io
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET


class ISODataSource(ABC):
    """Base class for ISO/RTO data sources."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/iso_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    @abstractmethod
    def fetch_current_prices(self) -> pd.DataFrame:
        """Fetch current/recent electricity prices."""
        pass
    
    @abstractmethod
    def fetch_historical_prices(self, date: datetime) -> pd.DataFrame:
        """Fetch historical prices for a specific date."""
        pass
    
    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize dataframe to common format."""
        # Ensure we have timestamp and price_per_mwh columns
        required_cols = ['timestamp', 'price_per_mwh']
        if all(col in df.columns for col in required_cols):
            return df[required_cols].sort_values('timestamp')
        return pd.DataFrame()


class NYISODataSource(ISODataSource):
    """
    New York Independent System Operator data source.
    Fetches real-time and day-ahead market prices.
    """
    
    # NYISO public data URLs
    BASE_URL = "http://mis.nyiso.com/public"
    
    def fetch_current_prices(self) -> pd.DataFrame:
        """
        Fetch current real-time market prices from NYISO.
        
        Returns:
            DataFrame with timestamp and price_per_mwh columns
        """
        try:
            print("Fetching NYISO real-time prices...")
            
            # NYISO provides CSV files with real-time prices
            # Format: http://mis.nyiso.com/public/csv/realtime/YYYYMMDD_realtime_gen.csv
            today = datetime.now()
            date_str = today.strftime("%Y%m%d")
            
            # Try real-time market LBMP (Locational Based Marginal Pricing)
            urls = [
                f"{self.BASE_URL}/csv/realtime/{date_str}realtime_zone.csv",
                f"{self.BASE_URL}/csv/damlbmp/{date_str}damlbmp_zone.csv",
                f"{self.BASE_URL}/P-24Alist.htm",  # Price list page
            ]
            
            for url in urls:
                try:
                    print(f"  Trying: {url}")
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        # Check if it's CSV data
                        if 'csv' in url and 'text' in response.headers.get('Content-Type', ''):
                            df = self._parse_nyiso_csv(response.text)
                            if not df.empty:
                                print(f"  ✓ Successfully parsed {len(df)} records")
                                return df
                        elif 'htm' in url:
                            # Parse HTML page for links to data files
                            return self._fetch_from_price_page(response.text)
                except Exception as e:
                    print(f"  ✗ Error: {str(e)[:50]}")
                    continue
            
            # If direct download fails, try the real-time dashboard API
            return self._fetch_from_dashboard()
            
        except Exception as e:
            print(f"Error fetching NYISO data: {e}")
            return pd.DataFrame()
    
    def _fetch_from_dashboard(self) -> pd.DataFrame:
        """Fetch data from NYISO's real-time dashboard."""
        try:
            # NYISO Real-Time Dashboard data endpoint
            url = "http://mis.nyiso.com/public/P-58Blist.htm"
            print(f"  Trying dashboard: {url}")
            
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                # Extract CSV links from the HTML page
                if 'realtime' in response.text.lower():
                    # Find the most recent real-time price file
                    import re
                    pattern = r'href="([^"]*realtime[^"]*\.csv)"'
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    
                    if matches:
                        csv_url = matches[0]
                        if not csv_url.startswith('http'):
                            csv_url = f"{self.BASE_URL}/{csv_url.lstrip('/')}"
                        
                        print(f"  Found CSV: {csv_url}")
                        csv_response = self.session.get(csv_url, timeout=15)
                        if csv_response.status_code == 200:
                            return self._parse_nyiso_csv(csv_response.text)
        except Exception as e:
            print(f"  Dashboard error: {e}")
        
        return pd.DataFrame()
    
    def _fetch_from_price_page(self, html_content: str) -> pd.DataFrame:
        """Extract and fetch price data from NYISO price page."""
        try:
            import re
            # Look for CSV file links in the HTML
            pattern = r'href="([^"]*\.csv)"'
            matches = re.findall(pattern, html_content)
            
            # Filter for real-time or day-ahead files
            for match in matches:
                if 'realtime' in match.lower() or 'damlbmp' in match.lower():
                    csv_url = match if match.startswith('http') else f"{self.BASE_URL}/{match}"
                    print(f"  Found price file: {csv_url}")
                    
                    response = self.session.get(csv_url, timeout=15)
                    if response.status_code == 200:
                        df = self._parse_nyiso_csv(response.text)
                        if not df.empty:
                            return df
        except Exception as e:
            print(f"  Price page error: {e}")
        
        return pd.DataFrame()
    
    def _parse_nyiso_csv(self, csv_text: str) -> pd.DataFrame:
        """Parse NYISO CSV format."""
        try:
            # NYISO CSV format varies, try to parse
            df = pd.read_csv(io.StringIO(csv_text))
            
            # Look for relevant columns
            # NYISO uses: Time Stamp, Name (zone), LBMP ($/MWHr)
            timestamp_cols = ['Time Stamp', 'Timestamp', 'Time', 'DATE']
            price_cols = ['LBMP ($/MWHr)', 'LBMP ($/MWH)', 'LBMP', 'Price', 'DAM LBMP', 'RT LBMP']
            zone_cols = ['Name', 'Zone', 'Zone Name', 'PTID Name']
            
            # Find matching columns
            time_col = next((col for col in df.columns if col in timestamp_cols), None)
            price_col = next((col for col in df.columns if any(pc in col for pc in price_cols)), None)
            zone_col = next((col for col in df.columns if col in zone_cols), None)
            
            if time_col and price_col:
                # Filter for a specific zone or take average
                if zone_col and 'N.Y.C.' in df[zone_col].values:
                    # Use NYC zone if available
                    df = df[df[zone_col] == 'N.Y.C.']
                elif zone_col and 'CAPITL' in df[zone_col].values:
                    # Use Capital zone (Albany area)
                    df = df[df[zone_col] == 'CAPITL']
                
                # Create standardized dataframe
                result_df = pd.DataFrame()
                result_df['timestamp'] = pd.to_datetime(df[time_col])
                result_df['price_per_mwh'] = pd.to_numeric(df[price_col], errors='coerce')
                
                # Remove any NaN values
                result_df = result_df.dropna()
                
                # If multiple prices for same timestamp, take average
                result_df = result_df.groupby('timestamp').mean().reset_index()
                
                return result_df.sort_values('timestamp')
            
        except Exception as e:
            print(f"  Parse error: {e}")
        
        return pd.DataFrame()
    
    def fetch_historical_prices(self, date: datetime) -> pd.DataFrame:
        """Fetch historical prices for a specific date."""
        date_str = date.strftime("%Y%m%d")
        
        # Check cache first
        cache_file = self.cache_dir / f"nyiso_{date_str}.parquet"
        if cache_file.exists():
            print(f"  Loading cached NYISO data for {date_str}")
            return pd.read_parquet(cache_file)
        
        # Try to fetch historical data
        urls = [
            f"{self.BASE_URL}/csv/damlbmp/{date_str}damlbmp_zone.csv",
            f"{self.BASE_URL}/csv/realtime/{date_str}realtime_zone.csv",
        ]
        
        for url in urls:
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    df = self._parse_nyiso_csv(response.text)
                    if not df.empty:
                        # Cache the data
                        df.to_parquet(cache_file)
                        return df
            except:
                continue
        
        return pd.DataFrame()


class PJMDataSource(ISODataSource):
    """
    PJM Interconnection data source.
    Covers Mid-Atlantic region including PA, NJ, MD, DE, VA, WV, OH, and more.
    """
    
    # PJM Data Miner API (public access)
    BASE_URL = "https://api.pjm.com/api/v1"
    DATA_MINER_URL = "https://dataminer2.pjm.com/feed/da_lmps/definition"
    
    def fetch_current_prices(self) -> pd.DataFrame:
        """Fetch current PJM electricity prices."""
        try:
            print("Fetching PJM real-time prices...")
            
            # PJM provides public data through their Data Miner 2 service
            # Try to get day-ahead LMP data
            today = datetime.now()
            
            # PJM public data feed
            urls = [
                f"https://dataminer2.pjm.com/feed/rt_lmps_prelimary/definition",
                f"https://dataminer2.pjm.com/feed/da_lmps/definition",
            ]
            
            for url in urls:
                try:
                    print(f"  Trying: {url}")
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        # PJM returns JSON with metadata
                        data = response.json()
                        
                        # Get the actual data URL from metadata
                        if 'items' in data:
                            for item in data['items']:
                                if 'name' in item:
                                    # Construct data URL
                                    data_url = f"https://dataminer2.pjm.com/feed/{item['name']}/data"
                                    return self._fetch_pjm_data(data_url)
                except Exception as e:
                    print(f"  ✗ Error: {str(e)[:50]}")
            
            # Alternative: Try simplified endpoint
            return self._fetch_pjm_simplified()
            
        except Exception as e:
            print(f"Error fetching PJM data: {e}")
            return pd.DataFrame()
    
    def _fetch_pjm_simplified(self) -> pd.DataFrame:
        """Fetch from simplified PJM endpoint."""
        try:
            # PJM provides a simplified LMP endpoint
            url = "https://www.pjm.com/pub/pricing/lmpnode/lmpnode.html"
            print(f"  Trying simplified endpoint: {url}")
            
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                # Parse HTML table or find CSV links
                if '.csv' in response.text:
                    import re
                    csv_pattern = r'href="([^"]*\.csv)"'
                    matches = re.findall(csv_pattern, response.text)
                    
                    for csv_link in matches[:3]:  # Try first 3 CSV files
                        if not csv_link.startswith('http'):
                            csv_link = f"https://www.pjm.com{csv_link}"
                        
                        try:
                            csv_response = self.session.get(csv_link, timeout=10)
                            if csv_response.status_code == 200:
                                df = self._parse_pjm_csv(csv_response.text)
                                if not df.empty:
                                    return df
                        except:
                            continue
        except Exception as e:
            print(f"  Simplified endpoint error: {e}")
        
        return pd.DataFrame()
    
    def _fetch_pjm_data(self, data_url: str) -> pd.DataFrame:
        """Fetch actual data from PJM data URL."""
        try:
            response = self.session.get(data_url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data)
                    return self._process_pjm_json(df)
        except:
            pass
        
        return pd.DataFrame()
    
    def _parse_pjm_csv(self, csv_text: str) -> pd.DataFrame:
        """Parse PJM CSV format."""
        try:
            df = pd.read_csv(io.StringIO(csv_text))
            
            # PJM columns typically include:
            # datetime_beginning_ept, pnode_name, total_lmp
            time_cols = ['datetime_beginning_ept', 'DateTime', 'Date', 'Hour']
            price_cols = ['total_lmp', 'LMP', 'System Price', 'RT LMP', 'DA LMP']
            
            time_col = next((col for col in df.columns if any(tc in col for tc in time_cols)), None)
            price_col = next((col for col in df.columns if any(pc in col for pc in price_cols)), None)
            
            if time_col and price_col:
                result_df = pd.DataFrame()
                result_df['timestamp'] = pd.to_datetime(df[time_col])
                result_df['price_per_mwh'] = pd.to_numeric(df[price_col], errors='coerce')
                
                # Take average if multiple nodes
                result_df = result_df.groupby('timestamp').mean().reset_index()
                
                return result_df.dropna().sort_values('timestamp')
        except Exception as e:
            print(f"  PJM parse error: {e}")
        
        return pd.DataFrame()
    
    def _process_pjm_json(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process PJM JSON data to standard format."""
        try:
            # Map PJM fields to standard format
            if 'datetime_beginning_ept' in df.columns and 'total_lmp' in df.columns:
                result_df = pd.DataFrame()
                result_df['timestamp'] = pd.to_datetime(df['datetime_beginning_ept'])
                result_df['price_per_mwh'] = pd.to_numeric(df['total_lmp'], errors='coerce')
                
                return result_df.dropna().sort_values('timestamp')
        except:
            pass
        
        return pd.DataFrame()
    
    def fetch_historical_prices(self, date: datetime) -> pd.DataFrame:
        """Fetch historical PJM prices."""
        # Implementation would query PJM Data Miner with specific date
        # For now, return empty DataFrame
        return pd.DataFrame()


class CAISODataSource(ISODataSource):
    """
    California Independent System Operator data source.
    Provides California electricity market prices.
    """
    
    # CAISO OASIS API (public)
    OASIS_URL = "http://oasis.caiso.com/oasisapi/SingleZip"
    
    def fetch_current_prices(self) -> pd.DataFrame:
        """Fetch current CAISO electricity prices."""
        try:
            print("Fetching CAISO real-time prices...")
            
            # CAISO OASIS API parameters
            today = datetime.now()
            
            params = {
                'queryname': 'PRC_LMP',  # Locational Marginal Prices
                'market_run_id': 'RTM',   # Real-Time Market
                'startdatetime': today.strftime('%Y%m%dT00:00-0000'),
                'enddatetime': today.strftime('%Y%m%dT23:59-0000'),
                'node': 'TH_SP15_GEN-APND',  # Southern California hub
                'resultformat': '6',  # CSV format
            }
            
            print(f"  Requesting CAISO OASIS data...")
            response = self.session.get(self.OASIS_URL, params=params, timeout=20)
            
            if response.status_code == 200:
                # CAISO returns a ZIP file with CSV inside
                return self._parse_caiso_zip(response.content)
            else:
                print(f"  ✗ Status: {response.status_code}")
            
            # Try alternative endpoint
            return self._fetch_caiso_alternative()
            
        except Exception as e:
            print(f"Error fetching CAISO data: {e}")
            return pd.DataFrame()
    
    def _fetch_caiso_alternative(self) -> pd.DataFrame:
        """Try alternative CAISO data source."""
        try:
            # CAISO Today's Outlook JSON feed
            url = "https://www.caiso.com/outlook/SP/prices.csv"
            print(f"  Trying alternative: {url}")
            
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.text))
                
                # Process CAISO format
                if 'Time' in df.columns and 'Price' in df.columns:
                    result_df = pd.DataFrame()
                    result_df['timestamp'] = pd.to_datetime(df['Time'])
                    result_df['price_per_mwh'] = pd.to_numeric(df['Price'], errors='coerce')
                    
                    return result_df.dropna().sort_values('timestamp')
        except Exception as e:
            print(f"  Alternative error: {e}")
        
        return pd.DataFrame()
    
    def _parse_caiso_zip(self, zip_content: bytes) -> pd.DataFrame:
        """Parse CAISO ZIP file containing CSV data."""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                # Find CSV file in the ZIP
                csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
                
                if csv_files:
                    with zf.open(csv_files[0]) as csv_file:
                        df = pd.read_csv(csv_file)
                        
                        # CAISO columns: INTERVALSTARTTIME_GMT, LMP
                        if 'INTERVALSTARTTIME_GMT' in df.columns and 'MW' in str(df.columns):
                            price_col = next((col for col in df.columns if 'LMP' in col or 'MW' in col), None)
                            
                            if price_col:
                                result_df = pd.DataFrame()
                                result_df['timestamp'] = pd.to_datetime(df['INTERVALSTARTTIME_GMT'])
                                result_df['price_per_mwh'] = pd.to_numeric(df[price_col], errors='coerce')
                                
                                return result_df.dropna().sort_values('timestamp')
        except Exception as e:
            print(f"  ZIP parse error: {e}")
        
        return pd.DataFrame()
    
    def fetch_historical_prices(self, date: datetime) -> pd.DataFrame:
        """Fetch historical CAISO prices."""
        # Would implement OASIS query for historical data
        return pd.DataFrame()


class UnifiedISOSource:
    """
    Unified interface for all ISO/RTO data sources.
    Provides simple access to electricity prices from multiple regions.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/iso_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize all ISO sources
        self.sources = {
            'NYISO': NYISODataSource(self.cache_dir),
            'PJM': PJMDataSource(self.cache_dir),
            'CAISO': CAISODataSource(self.cache_dir),
            'ERCOT': None  # Use existing ERCOT implementation
        }
    
    def fetch_all_current_prices(self) -> Dict[str, pd.DataFrame]:
        """
        Fetch current prices from all available ISOs.
        
        Returns:
            Dictionary mapping ISO name to price DataFrame
        """
        results = {}
        
        for iso_name, source in self.sources.items():
            if source is None:
                continue
                
            print(f"\nFetching {iso_name} prices...")
            try:
                df = source.fetch_current_prices()
                if not df.empty:
                    results[iso_name] = df
                    print(f"  ✓ Got {len(df)} records from {iso_name}")
                else:
                    print(f"  ✗ No data from {iso_name}")
            except Exception as e:
                print(f"  ✗ Error with {iso_name}: {e}")
        
        return results
    
    def fetch_iso_prices(self, iso: str) -> pd.DataFrame:
        """
        Fetch prices from a specific ISO.
        
        Args:
            iso: ISO name ('NYISO', 'PJM', 'CAISO')
            
        Returns:
            DataFrame with electricity prices
        """
        if iso not in self.sources:
            raise ValueError(f"Unknown ISO: {iso}. Choose from: {list(self.sources.keys())}")
        
        source = self.sources[iso]
        if source is None:
            return pd.DataFrame()
        
        return source.fetch_current_prices()


def test_iso_sources():
    """Test all ISO data sources."""
    print("Testing ISO/RTO Data Sources")
    print("=" * 60)
    
    unified = UnifiedISOSource()
    
    # Test each ISO individually
    for iso in ['NYISO', 'PJM', 'CAISO']:
        print(f"\nTesting {iso}...")
        df = unified.fetch_iso_prices(iso)
        
        if not df.empty:
            print(f"✓ {iso}: {len(df)} records")
            print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"  Price range: ${df['price_per_mwh'].min():.2f} - ${df['price_per_mwh'].max():.2f}/MWh")
            print(f"  Mean: ${df['price_per_mwh'].mean():.2f}/MWh")
        else:
            print(f"✗ {iso}: No data retrieved")
    
    # Test fetching all at once
    print("\n" + "=" * 60)
    print("Fetching all ISOs simultaneously...")
    all_data = unified.fetch_all_current_prices()
    
    print(f"\nSuccessfully retrieved data from {len(all_data)} ISOs:")
    for iso, df in all_data.items():
        print(f"  {iso}: {len(df)} records")
    
    return all_data


if __name__ == "__main__":
    test_iso_sources()