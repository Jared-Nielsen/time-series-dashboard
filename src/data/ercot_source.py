"""
ERCOT (Texas) electricity price data source.
Fetches real-time and historical price data from ERCOT's public data portal.
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json
from pathlib import Path
import zipfile
import io


class ERCOTDataSource:
    """
    ERCOT data source for Texas electricity prices.
    Uses ERCOT's public data API (no authentication required).
    """
    
    # ERCOT Public API endpoints
    BASE_URL = "https://www.ercot.com"
    API_BASE = "https://api.ercot.com/api/public-reports"
    
    # Report types for different price data
    REPORT_TYPES = {
        "dam_spp": "NP4-190-CD",  # Day-Ahead Market Settlement Point Prices
        "rtm_spp": "NP6-905-CD",  # Real-Time Market Settlement Point Prices  
        "dam_clearing": "NP4-183-CD",  # Day-Ahead Market Clearing Prices for Capacity
    }
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize ERCOT data source."""
        self.cache_dir = cache_dir or Path("data/ercot_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
    
    def fetch_dam_prices(self, 
                        date: Optional[datetime] = None,
                        settlement_point: str = "HB_HOUSTON") -> pd.DataFrame:
        """
        Fetch Day-Ahead Market (DAM) Settlement Point Prices.
        
        Args:
            date: Date to fetch prices for (default: yesterday)
            settlement_point: Settlement point/hub (default: Houston Hub)
            
        Returns:
            DataFrame with hourly DAM prices
        """
        if not date:
            date = datetime.now() - timedelta(days=1)
        
        # Try the data portal CSV endpoint
        return self._fetch_from_data_portal(date, "DAM", settlement_point)
    
    def fetch_rtm_prices(self,
                        date: Optional[datetime] = None,
                        settlement_point: str = "HB_HOUSTON") -> pd.DataFrame:
        """
        Fetch Real-Time Market (RTM) Settlement Point Prices.
        
        Args:
            date: Date to fetch prices for (default: yesterday)
            settlement_point: Settlement point/hub (default: Houston Hub)
            
        Returns:
            DataFrame with 15-minute RTM prices
        """
        if not date:
            date = datetime.now() - timedelta(days=1)
        
        return self._fetch_from_data_portal(date, "RTM", settlement_point)
    
    def _fetch_from_data_portal(self, 
                                date: datetime,
                                market_type: str,
                                settlement_point: str) -> pd.DataFrame:
        """
        Fetch data from ERCOT's public data portal.
        
        ERCOT provides data through their MIS (Market Information System) portal.
        """
        # Format date for ERCOT API
        date_str = date.strftime("%Y%m%d")
        
        # ERCOT MIS Public Reports URL pattern
        if market_type == "DAM":
            # Day-Ahead Market SPP report
            report_name = f"DA_SPP_{date_str}"
            url = f"https://www.ercot.com/content/cdr/html/{date_str}_dam_spp.html"
            
            # Alternative: Try direct file download
            csv_url = f"https://www.ercot.com/content/cdr/csv/{date_str}_dam_spp.csv"
        else:
            # Real-Time Market SPP report  
            report_name = f"RTM_SPP_{date_str}"
            url = f"https://www.ercot.com/content/cdr/html/{date_str}_real_time_spp.html"
            csv_url = f"https://www.ercot.com/content/cdr/csv/{date_str}_real_time_spp.csv"
        
        # Check cache first
        cache_file = self.cache_dir / f"{report_name}_{settlement_point}.parquet"
        if cache_file.exists():
            print(f"Loading cached data from {cache_file}")
            return pd.read_parquet(cache_file)
        
        # Try to download the CSV directly
        try:
            print(f"Attempting to download {market_type} prices for {date_str}...")
            print(f"URL: {csv_url}")
            
            response = self.session.get(csv_url, timeout=30)
            
            if response.status_code == 200:
                # Parse CSV data
                df = self._parse_spp_csv(response.text, market_type, settlement_point)
                
                # Cache the data
                if not df.empty:
                    df.to_parquet(cache_file)
                    print(f"Cached data to {cache_file}")
                
                return df
            else:
                print(f"Failed to download: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"Error downloading from ERCOT: {e}")
        
        # If direct download fails, try the API approach
        return self._fetch_from_api(date, market_type, settlement_point)
    
    def _fetch_from_api(self,
                       date: datetime,
                       market_type: str,
                       settlement_point: str) -> pd.DataFrame:
        """
        Alternative method using ERCOT's Data API.
        """
        # ERCOT Data API endpoint (if available)
        # Note: ERCOT's API structure changes, this is a common pattern
        
        date_str = date.strftime("%m/%d/%Y")
        
        params = {
            "reportTypeId": self.REPORT_TYPES.get(f"{market_type.lower()}_spp", ""),
            "deliveryDate": date_str,
            "settlementPoint": settlement_point
        }
        
        try:
            print(f"Trying ERCOT API for {market_type} prices...")
            response = self.session.get(
                f"{self.API_BASE}/archive",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_api_response(data, market_type)
            else:
                print(f"API request failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"API error: {e}")
        
        return pd.DataFrame()
    
    def _parse_spp_csv(self, 
                      csv_text: str,
                      market_type: str,
                      settlement_point: str) -> pd.DataFrame:
        """
        Parse ERCOT SPP CSV format.
        """
        try:
            # Read CSV, skipping header rows if present
            df = pd.read_csv(io.StringIO(csv_text), skiprows=0)
            
            # ERCOT CSV columns typically include:
            # DeliveryDate, DeliveryHour, DeliveryInterval, SettlementPoint, Price
            
            # Standardize column names
            column_mapping = {
                'DeliveryDate': 'date',
                'Delivery Date': 'date',
                'DeliveryHour': 'hour',
                'Delivery Hour': 'hour', 
                'DeliveryInterval': 'interval',
                'Delivery Interval': 'interval',
                'SettlementPoint': 'settlement_point',
                'Settlement Point': 'settlement_point',
                'Settlement Point Name': 'settlement_point',
                'SPP': 'settlement_point',
                'Price': 'price',
                'SPP Price': 'price',
                'Settlement Point Price': 'price'
            }
            
            # Rename columns
            df.columns = [column_mapping.get(col, col.lower().replace(' ', '_')) 
                         for col in df.columns]
            
            # Filter for specific settlement point if it exists
            if 'settlement_point' in df.columns and settlement_point:
                df = df[df['settlement_point'].str.contains(settlement_point, case=False, na=False)]
            
            # Create timestamp column
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                
                if 'hour' in df.columns:
                    # For hourly data (DAM)
                    df['timestamp'] = df['date'] + pd.to_timedelta(df['hour'] - 1, unit='h')
                elif 'interval' in df.columns:
                    # For 15-minute data (RTM)
                    df['timestamp'] = df['date'] + pd.to_timedelta((df['interval'] - 1) * 15, unit='m')
                else:
                    df['timestamp'] = df['date']
            
            # Standardize output format
            if 'price' in df.columns and 'timestamp' in df.columns:
                result_df = df[['timestamp', 'price']].copy()
                result_df.columns = ['timestamp', 'price_per_mwh']
                result_df = result_df.sort_values('timestamp')
                return result_df
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"Error parsing CSV: {e}")
            return pd.DataFrame()
    
    def _parse_api_response(self, data: Dict, market_type: str) -> pd.DataFrame:
        """
        Parse ERCOT API JSON response.
        """
        try:
            if 'data' in data:
                df = pd.DataFrame(data['data'])
                # Process similar to CSV parsing
                return self._standardize_dataframe(df)
            return pd.DataFrame()
        except Exception as e:
            print(f"Error parsing API response: {e}")
            return pd.DataFrame()
    
    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize DataFrame to common format.
        """
        # Ensure we have timestamp and price columns
        if 'timestamp' not in df.columns:
            # Try to create timestamp from other columns
            if 'date' in df.columns and 'hour' in df.columns:
                df['timestamp'] = pd.to_datetime(df['date']) + pd.to_timedelta(df['hour'], unit='h')
        
        if 'price_per_mwh' not in df.columns:
            # Look for price column
            price_cols = [col for col in df.columns if 'price' in col.lower()]
            if price_cols:
                df['price_per_mwh'] = df[price_cols[0]]
        
        # Return standardized format
        if 'timestamp' in df.columns and 'price_per_mwh' in df.columns:
            return df[['timestamp', 'price_per_mwh']].sort_values('timestamp')
        
        return pd.DataFrame()
    
    def fetch_historical_data(self,
                            start_date: datetime,
                            end_date: datetime,
                            market_type: str = "DAM",
                            settlement_point: str = "HB_HOUSTON") -> pd.DataFrame:
        """
        Fetch historical data for a date range.
        
        Args:
            start_date: Start of period
            end_date: End of period
            market_type: 'DAM' or 'RTM'
            settlement_point: Settlement point name
            
        Returns:
            Combined DataFrame for the period
        """
        all_data = []
        current_date = start_date
        
        while current_date <= end_date:
            print(f"Fetching {market_type} data for {current_date.strftime('%Y-%m-%d')}...")
            
            if market_type == "DAM":
                df = self.fetch_dam_prices(current_date, settlement_point)
            else:
                df = self.fetch_rtm_prices(current_date, settlement_point)
            
            if not df.empty:
                all_data.append(df)
            
            current_date += timedelta(days=1)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['timestamp'])
            combined_df = combined_df.sort_values('timestamp')
            return combined_df
        
        return pd.DataFrame()


def test_ercot_connection():
    """Test ERCOT data source connectivity."""
    print("Testing ERCOT data source...")
    print("="*60)
    
    source = ERCOTDataSource()
    
    # Test with a recent date
    test_date = datetime.now() - timedelta(days=2)
    
    print(f"\nFetching DAM prices for {test_date.strftime('%Y-%m-%d')}...")
    dam_df = source.fetch_dam_prices(test_date)
    
    if not dam_df.empty:
        print(f"✓ Successfully fetched {len(dam_df)} DAM price records")
        print(f"  Date range: {dam_df['timestamp'].min()} to {dam_df['timestamp'].max()}")
        print(f"  Average price: ${dam_df['price_per_mwh'].mean():.2f}/MWh")
        print("\nFirst 5 records:")
        print(dam_df.head())
    else:
        print("✗ No DAM data retrieved")
    
    return dam_df