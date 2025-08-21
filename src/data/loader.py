"""
Data loader module for electricity price data.
Handles loading from various sources and caching.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union, Dict, Any
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from .sources import get_data_source, DataSource
from .ercot_live import ERCOTLiveSource
from .iso_sources_v2 import AllISOSource, NYISOSource, PJMSource, CAISOSource, MISOSource

# Load environment variables
load_dotenv()


class DataLoader:
    """Main data loader class that handles multiple data sources."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize data loader.
        
        Args:
            cache_dir: Directory for caching downloaded data
        """
        self.cache_dir = cache_dir or Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def load_sample_data(self, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         frequency: str = "h") -> pd.DataFrame:
        """
        Load sample/synthetic electricity price data.
        
        Args:
            start_date: Start of data period
            end_date: End of data period
            frequency: Data frequency ('h' for hourly, 'D' for daily)
        
        Returns:
            DataFrame with timestamp and price_per_mwh columns
        """
        source = get_data_source("sample")
        return source.fetch(start_date, end_date, frequency)
    
    def load_eia_data(self,
                      region: str = "NYIS",
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      use_cache: bool = True) -> pd.DataFrame:
        """
        Load electricity price data from EIA API.
        
        Args:
            region: ISO/RTO region code ('NYIS', 'PJM', 'CAISO', 'ERCOT', etc.)
            start_date: Start of data period
            end_date: End of data period
            use_cache: Whether to use cached data if available
        
        Returns:
            DataFrame with timestamp and price_per_mwh columns
        """
        # Check for cached data
        cache_file = self.cache_dir / f"eia_{region}_{start_date}_{end_date}.parquet"
        
        if use_cache and cache_file.exists():
            print(f"Loading cached data from {cache_file}")
            return pd.read_parquet(cache_file)
        
        # Fetch fresh data
        print(f"Fetching data from EIA API for region {region}...")
        source = get_data_source("eia")
        df = source.fetch(start_date, end_date, region)
        
        # Cache the data
        if use_cache:
            df.to_parquet(cache_file)
            print(f"Cached data to {cache_file}")
        
        return df
    
    def load_csv_data(self,
                      file_path: Union[str, Path],
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Load electricity price data from CSV file.
        
        Args:
            file_path: Path to CSV file
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            DataFrame with timestamp and price_per_mwh columns
        """
        source = get_data_source("csv", file_path=file_path)
        return source.fetch(start_date, end_date)
    
    def load_ercot_data(self, 
                       aggregation: str = "raw") -> pd.DataFrame:
        """
        Load live electricity price data from ERCOT (Texas).
        
        Args:
            aggregation: 'raw' for all data points, 'hourly' for hourly averages
        
        Returns:
            DataFrame with timestamp and price_per_mwh columns
        """
        print("Loading ERCOT real-time electricity prices...")
        source = ERCOTLiveSource(cache_dir=self.cache_dir)
        
        if aggregation == "hourly":
            return source.fetch_aggregated_hourly()
        else:
            return source.fetch_recent_prices()
    
    def load_iso_data(self, 
                     iso: str = "all",
                     include_simulated: bool = True) -> pd.DataFrame:
        """
        Load electricity price data from US ISOs/RTOs.
        
        Args:
            iso: ISO name ('NYISO', 'PJM', 'CAISO', 'MISO', 'ERCOT') or 'all'
            include_simulated: Whether to include simulated data for ISOs without API access
        
        Returns:
            DataFrame with timestamp, price_per_mwh, zone, and iso columns
        """
        all_iso = AllISOSource()
        
        if iso.upper() == "ALL":
            print("Loading data from all ISOs...")
            df = all_iso.fetch_all_prices()
            
            # Add ERCOT data
            try:
                ercot_source = ERCOTLiveSource(cache_dir=self.cache_dir)
                ercot_df = ercot_source.fetch_aggregated_hourly()
                if not ercot_df.empty:
                    # Remove timezone info to match other data
                    if ercot_df['timestamp'].dt.tz is not None:
                        ercot_df['timestamp'] = ercot_df['timestamp'].dt.tz_localize(None)
                    ercot_df['zone'] = 'Houston'
                    ercot_df['iso'] = 'ERCOT'
                    df = pd.concat([df, ercot_df], ignore_index=True)
                    print(f"✓ ERCOT: {len(ercot_df)} records")
            except Exception as e:
                print(f"✗ ERCOT: {str(e)[:50]}")
            
            if not include_simulated and not df.empty:
                # Filter out simulated data (PJM, CAISO, MISO are simulated)
                df = df[df['iso'].isin(['NYISO', 'ERCOT'])]
                print(f"Filtered to real data only: {len(df)} records")
            
            return df
        
        elif iso.upper() == "ERCOT":
            # Special handling for ERCOT
            print(f"Loading {iso.upper()} data...")
            source = ERCOTLiveSource(cache_dir=self.cache_dir)
            df = source.fetch_aggregated_hourly()
            if not df.empty:
                # Remove timezone info to match other data
                if df['timestamp'].dt.tz is not None:
                    df['timestamp'] = df['timestamp'].dt.tz_localize(None)
                df['zone'] = 'Houston'
                df['iso'] = 'ERCOT'
            return df
        
        else:
            # Load specific ISO
            print(f"Loading {iso.upper()} data...")
            df = all_iso.fetch_iso(iso.upper())
            
            if not include_simulated and iso.upper() in ['PJM', 'CAISO', 'MISO']:
                print(f"Note: {iso.upper()} data is simulated. Set include_simulated=True to retrieve.")
                return pd.DataFrame()
            
            return df
    
    def load_nyiso_data(self) -> pd.DataFrame:
        """Load NYISO (New York) electricity prices."""
        source = NYISOSource(cache_dir=self.cache_dir)
        return source.fetch_current_prices()
    
    def load_data(self,
                  source: str = "sample",
                  **kwargs) -> pd.DataFrame:
        """
        Generic data loading method.
        
        Args:
            source: Data source type ('sample', 'eia', 'csv', 'ercot', 'iso', 'nyiso')
            **kwargs: Additional arguments for the specific source
        
        Returns:
            DataFrame with timestamp and price_per_mwh columns
        """
        if source == "sample":
            return self.load_sample_data(**kwargs)
        elif source == "eia":
            return self.load_eia_data(**kwargs)
        elif source == "csv":
            return self.load_csv_data(**kwargs)
        elif source == "ercot":
            return self.load_ercot_data(**kwargs)
        elif source == "iso":
            return self.load_iso_data(**kwargs)
        elif source == "nyiso":
            return self.load_nyiso_data(**kwargs)
        else:
            raise ValueError(f"Unknown source: {source}")
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate electricity price data.
        
        Args:
            df: DataFrame to validate
        
        Returns:
            Dictionary with validation results
        """
        results = {
            "valid": True,
            "issues": [],
            "stats": {}
        }
        
        # Check required columns
        required_cols = ["timestamp", "price_per_mwh"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["valid"] = False
            results["issues"].append(f"Missing columns: {missing_cols}")
        
        # Check data types
        if "timestamp" in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
                results["issues"].append("timestamp column is not datetime type")
        
        if "price_per_mwh" in df.columns:
            if not pd.api.types.is_numeric_dtype(df["price_per_mwh"]):
                results["valid"] = False
                results["issues"].append("price_per_mwh column is not numeric")
        
        # Check for missing values
        null_counts = df.isnull().sum()
        if null_counts.any():
            results["issues"].append(f"Missing values: {null_counts[null_counts > 0].to_dict()}")
        
        # Check for negative prices (allowed but flag as warning)
        if "price_per_mwh" in df.columns:
            negative_prices = df["price_per_mwh"] < 0
            if negative_prices.any():
                results["issues"].append(f"Found {negative_prices.sum()} negative prices")
        
        # Calculate statistics
        if "price_per_mwh" in df.columns:
            results["stats"] = {
                "count": len(df),
                "mean_price": df["price_per_mwh"].mean(),
                "std_price": df["price_per_mwh"].std(),
                "min_price": df["price_per_mwh"].min(),
                "max_price": df["price_per_mwh"].max(),
                "date_range": (df["timestamp"].min(), df["timestamp"].max()) if "timestamp" in df.columns else None
            }
        
        return results


def quick_load(source: str = "sample", **kwargs) -> pd.DataFrame:
    """
    Convenience function for quick data loading.
    
    Args:
        source: Data source type
        **kwargs: Source-specific arguments
    
    Returns:
        DataFrame with electricity price data
    """
    loader = DataLoader()
    return loader.load_data(source, **kwargs)