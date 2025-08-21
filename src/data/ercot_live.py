"""
ERCOT Live Data Source - Real-time electricity prices from Texas.
Uses ERCOT's public dashboard API (no authentication required).
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path


class ERCOTLiveSource:
    """
    Fetches real-time and recent electricity price data from ERCOT's public dashboard.
    """
    
    # ERCOT Dashboard API endpoints
    DASHBOARD_URL = "https://www.ercot.com/api/1/services/read/dashboards/daily-prc.json"
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize ERCOT live data source."""
        self.cache_dir = cache_dir or Path("data/ercot_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_recent_prices(self) -> pd.DataFrame:
        """
        Fetch recent real-time electricity prices from ERCOT dashboard.
        
        Returns:
            DataFrame with timestamp and price_per_mwh columns
        """
        try:
            print("Fetching live ERCOT electricity prices...")
            response = requests.get(self.DASHBOARD_URL, timeout=15)
            
            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}")
                return pd.DataFrame()
            
            data = response.json()
            
            # Extract the time series data
            if 'data' not in data:
                print("No data field in response")
                return pd.DataFrame()
            
            df = pd.DataFrame(data['data'])
            
            # Convert to standard format
            if 'timestamp' in df.columns and 'prc' in df.columns:
                # Parse timestamp and remove timezone for consistency
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                if df['timestamp'].dt.tz is not None:
                    df['timestamp'] = df['timestamp'].dt.tz_localize(None)
                
                # Convert price from tenths of cents to dollars per MWh
                # ERCOT reports in tenths of cents per kWh
                # So divide by 10 to get cents/kWh, then multiply by 10 to get $/MWh
                # Net effect: just divide by 1
                df['price_per_mwh'] = df['prc'] / 100  # Convert to $/MWh
                
                # Select and sort
                result_df = df[['timestamp', 'price_per_mwh']].copy()
                result_df = result_df.sort_values('timestamp')
                
                # Remove duplicates if any
                result_df = result_df.drop_duplicates(subset=['timestamp'])
                
                # Cache the data
                cache_file = self.cache_dir / f"ercot_live_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
                result_df.to_parquet(cache_file)
                print(f"Cached {len(result_df)} records to {cache_file}")
                
                return result_df
            else:
                print(f"Unexpected columns: {df.columns.tolist()}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error fetching ERCOT data: {e}")
            return pd.DataFrame()
    
    def fetch_aggregated_hourly(self) -> pd.DataFrame:
        """
        Fetch recent prices and aggregate to hourly averages.
        
        Returns:
            DataFrame with hourly averaged prices
        """
        # Get raw data
        df = self.fetch_recent_prices()
        
        if df.empty:
            return df
        
        # Set timestamp as index for resampling
        df = df.set_index('timestamp')
        
        # Resample to hourly averages
        hourly_df = df.resample('h').mean()
        hourly_df = hourly_df.reset_index()
        
        print(f"Aggregated to {len(hourly_df)} hourly records")
        
        return hourly_df
    
    def get_latest_price(self) -> Optional[float]:
        """
        Get the most recent electricity price.
        
        Returns:
            Latest price in $/MWh or None if unavailable
        """
        df = self.fetch_recent_prices()
        
        if not df.empty:
            latest = df.iloc[-1]
            print(f"Latest ERCOT price: ${latest['price_per_mwh']:.2f}/MWh at {latest['timestamp']}")
            return latest['price_per_mwh']
        
        return None
    
    def get_daily_stats(self) -> dict:
        """
        Get daily statistics for electricity prices.
        
        Returns:
            Dictionary with min, max, mean, std prices for the day
        """
        df = self.fetch_recent_prices()
        
        if df.empty:
            return {}
        
        # Filter to today's data
        today = pd.Timestamp.now().normalize()
        df_today = df[df['timestamp'] >= today]
        
        if df_today.empty:
            # Use all available data if no data for today
            df_today = df
        
        stats = {
            'date': today.strftime('%Y-%m-%d'),
            'count': len(df_today),
            'mean': df_today['price_per_mwh'].mean(),
            'std': df_today['price_per_mwh'].std(),
            'min': df_today['price_per_mwh'].min(),
            'max': df_today['price_per_mwh'].max(),
            'median': df_today['price_per_mwh'].median(),
            'last_update': df_today['timestamp'].max()
        }
        
        print(f"Daily stats for {stats['date']}:")
        print(f"  Mean: ${stats['mean']:.2f}/MWh")
        print(f"  Range: ${stats['min']:.2f} - ${stats['max']:.2f}/MWh")
        print(f"  Records: {stats['count']}")
        
        return stats


def test_ercot_live():
    """Test the ERCOT live data source."""
    print("Testing ERCOT Live Data Source")
    print("="*60)
    
    source = ERCOTLiveSource()
    
    # Test fetching recent prices
    print("\n1. Fetching recent prices...")
    df = source.fetch_recent_prices()
    
    if not df.empty:
        print(f"✓ Fetched {len(df)} price records")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"Price range: ${df['price_per_mwh'].min():.2f} - ${df['price_per_mwh'].max():.2f}/MWh")
        print("\nFirst 5 records:")
        print(df.head())
        print("\nLast 5 records:")
        print(df.tail())
    else:
        print("✗ No data fetched")
        return
    
    # Test hourly aggregation
    print("\n2. Testing hourly aggregation...")
    hourly_df = source.fetch_aggregated_hourly()
    if not hourly_df.empty:
        print(f"✓ Aggregated to {len(hourly_df)} hourly records")
        print(hourly_df.head())
    
    # Test latest price
    print("\n3. Getting latest price...")
    latest = source.get_latest_price()
    if latest:
        print(f"✓ Latest price: ${latest:.2f}/MWh")
    
    # Test daily stats
    print("\n4. Getting daily statistics...")
    stats = source.get_daily_stats()
    if stats:
        print("✓ Daily statistics calculated")
    
    return df


if __name__ == "__main__":
    test_ercot_live()