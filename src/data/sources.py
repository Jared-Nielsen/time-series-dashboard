"""
Electricity price data source implementations.
Provides access to various public electricity price datasets.
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import io
import os
from pathlib import Path


class DataSource:
    """Base class for electricity price data sources."""
    
    def fetch(self, start_date: Optional[datetime] = None, 
              end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Fetch data from the source."""
        raise NotImplementedError


class EIADataSource(DataSource):
    """
    U.S. Energy Information Administration (EIA) API
    Provides wholesale electricity prices for various US regions.
    Free API key required from: https://www.eia.gov/opendata/
    """
    
    BASE_URL = "https://api.eia.gov/v2/electricity/wholesale-prices/data"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("EIA_API_KEY")
        if not self.api_key:
            raise ValueError("EIA API key required. Get one at https://www.eia.gov/opendata/")
    
    def fetch(self, start_date: Optional[datetime] = None,
              end_date: Optional[datetime] = None,
              region: str = "NYIS") -> pd.DataFrame:
        """
        Fetch wholesale electricity prices from EIA.
        
        Args:
            start_date: Start of data period
            end_date: End of data period  
            region: ISO/RTO region code (e.g., 'NYIS', 'PJM', 'CAISO', 'ERCOT')
        """
        params = {
            "api_key": self.api_key,
            "frequency": "hourly",
            "data[0]": "price",
            "facets[respondent][]": region,
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "offset": 0,
            "length": 5000
        }
        
        if start_date:
            params["start"] = start_date.strftime("%Y-%m-%dT%H")
        if end_date:
            params["end"] = end_date.strftime("%Y-%m-%dT%H")
        
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        df = pd.DataFrame(data["response"]["data"])
        
        df["timestamp"] = pd.to_datetime(df["period"])
        df = df.rename(columns={"price": "price_per_mwh"})
        df = df[["timestamp", "price_per_mwh"]]
        df = df.sort_values("timestamp")
        
        return df


class EntsoEDataSource(DataSource):
    """
    ENTSO-E Transparency Platform
    European electricity market data.
    API token required from: https://transparency.entsoe.eu/
    """
    
    BASE_URL = "https://web-api.tp.entsoe.eu/api"
    
    AREA_CODES = {
        "DE": "10Y1001A1001A83F",  # Germany
        "FR": "10YFR-RTE------C",  # France
        "ES": "10YES-REE------0",  # Spain
        "UK": "10Y1001A1001A92E",  # United Kingdom
        "IT": "10YIT-GRTN-----B",  # Italy
        "NL": "10YNL----------L",  # Netherlands
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ENTSOE_API_KEY")
        if not self.api_key:
            raise ValueError("ENTSO-E API key required. Get one at https://transparency.entsoe.eu/")
    
    def fetch(self, start_date: Optional[datetime] = None,
              end_date: Optional[datetime] = None,
              country: str = "DE") -> pd.DataFrame:
        """
        Fetch day-ahead electricity prices from ENTSO-E.
        
        Args:
            start_date: Start of data period
            end_date: End of data period
            country: Country code (e.g., 'DE', 'FR', 'ES')
        """
        if country not in self.AREA_CODES:
            raise ValueError(f"Country {country} not supported. Use one of: {list(self.AREA_CODES.keys())}")
        
        params = {
            "securityToken": self.api_key,
            "documentType": "A44",  # Day-ahead prices
            "in_Domain": self.AREA_CODES[country],
            "out_Domain": self.AREA_CODES[country],
            "periodStart": start_date.strftime("%Y%m%d%H%M"),
            "periodEnd": end_date.strftime("%Y%m%d%H%M")
        }
        
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        
        # Parse XML response (simplified - would need proper XML parsing)
        # This is a placeholder for actual XML parsing logic
        # In production, use libraries like xml.etree.ElementTree or lxml
        
        # For now, return sample structure
        raise NotImplementedError("ENTSO-E XML parsing to be implemented")


class SampleDataSource(DataSource):
    """
    Generate sample electricity price data for testing.
    Creates realistic synthetic data with daily and seasonal patterns.
    """
    
    def fetch(self, start_date: Optional[datetime] = None,
              end_date: Optional[datetime] = None,
              frequency: str = "h") -> pd.DataFrame:
        """
        Generate sample electricity price data.
        
        Args:
            start_date: Start of data period (default: 1 year ago)
            end_date: End of data period (default: today)
            frequency: Data frequency ('h' for hourly, 'D' for daily)
        """
        import numpy as np
        
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=365)
        
        # Generate timestamp index
        timestamps = pd.date_range(start=start_date, end=end_date, freq=frequency)
        n_points = len(timestamps)
        
        # Base price with trend
        base_price = 50
        trend = np.linspace(0, 10, n_points)
        
        # Daily pattern (higher during day, lower at night)
        hours = np.array([t.hour for t in timestamps])
        daily_pattern = 10 * np.sin((hours - 6) * np.pi / 12)
        daily_pattern[hours < 6] = -5
        daily_pattern[hours > 22] = -5
        
        # Weekly pattern (higher on weekdays)
        weekdays = np.array([t.weekday() for t in timestamps])
        weekly_pattern = np.where(weekdays < 5, 5, -5)
        
        # Seasonal pattern
        days_in_year = np.array([t.dayofyear for t in timestamps])
        seasonal_pattern = 15 * np.sin((days_in_year - 80) * 2 * np.pi / 365)
        
        # Random noise
        noise = np.random.normal(0, 5, n_points)
        
        # Combine all components
        prices = base_price + trend + daily_pattern + weekly_pattern + seasonal_pattern + noise
        
        # Add occasional spikes (extreme weather events)
        spike_prob = 0.02
        spikes = np.random.random(n_points) < spike_prob
        prices[spikes] *= np.random.uniform(1.5, 3.0, size=spikes.sum())
        
        # Ensure no negative prices
        prices = np.maximum(prices, 1)
        
        df = pd.DataFrame({
            "timestamp": timestamps,
            "price_per_mwh": prices
        })
        
        return df


class CSVDataSource(DataSource):
    """Load electricity price data from local CSV files."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    def fetch(self, start_date: Optional[datetime] = None,
              end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Load data from CSV file.
        
        Expected columns: 'timestamp' or 'date', and 'price' or similar.
        """
        df = pd.read_csv(self.file_path)
        
        # Try to identify timestamp column
        time_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
        if not time_cols:
            raise ValueError("No timestamp column found in CSV")
        
        # Try to identify price column
        price_cols = [col for col in df.columns if 'price' in col.lower() or 'cost' in col.lower()]
        if not price_cols:
            # Use first numeric column after timestamp
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
            if not numeric_cols:
                raise ValueError("No price column found in CSV")
            price_cols = [numeric_cols[0]]
        
        # Standardize column names
        df["timestamp"] = pd.to_datetime(df[time_cols[0]])
        df["price_per_mwh"] = df[price_cols[0]]
        df = df[["timestamp", "price_per_mwh"]]
        
        # Filter by date range if specified
        if start_date:
            df = df[df["timestamp"] >= start_date]
        if end_date:
            df = df[df["timestamp"] <= end_date]
        
        df = df.sort_values("timestamp")
        return df


def get_data_source(source_type: str, **kwargs) -> DataSource:
    """
    Factory function to create data source instances.
    
    Args:
        source_type: Type of data source ('sample', 'eia', 'entsoe', 'csv')
        **kwargs: Additional arguments for the specific data source
    
    Returns:
        DataSource instance
    """
    sources = {
        "sample": SampleDataSource,
        "eia": EIADataSource,
        "entsoe": EntsoEDataSource,
        "csv": CSVDataSource
    }
    
    if source_type not in sources:
        raise ValueError(f"Unknown source type: {source_type}. Choose from: {list(sources.keys())}")
    
    return sources[source_type](**kwargs)