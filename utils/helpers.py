"""
Helper functions for data processing utilities.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import re


def read_csv_flexible(file_path: Path) -> pd.DataFrame:
    """
    Read CSV file with flexible encoding handling.
    Tries multiple encodings to handle various file formats.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame containing the CSV data
    """
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
            return df
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    # If all encodings fail, try with error handling
    return pd.read_csv(file_path, encoding='utf-8', errors='replace', low_memory=False)


def clean_numeric_column(series: pd.Series) -> pd.Series:
    """
    Clean numeric column by removing commas, converting to numeric, and handling errors.
    
    Args:
        series: Pandas Series containing numeric data (may be strings with commas)
        
    Returns:
        Series with cleaned numeric values (NaN for non-numeric values)
    """
    if series.dtype == 'object':
        # Remove commas and other non-numeric characters except decimal points and minus signs
        cleaned = series.astype(str).str.replace(',', '', regex=False)
        cleaned = cleaned.str.strip()
        # Replace empty strings with NaN
        cleaned = cleaned.replace(['', 'nan', 'None', 'null'], np.nan)
    else:
        cleaned = series
    
    # Convert to numeric, coercing errors to NaN
    return pd.to_numeric(cleaned, errors='coerce')


def normalize_county_name(county_name: str) -> Optional[str]:
    """
    Normalize county name by removing common suffixes and standardizing format.
    
    Args:
        county_name: Raw county name string
        
    Returns:
        Normalized county name, or None if input is invalid
    """
    if not county_name or pd.isna(county_name):
        return None
    
    county_str = str(county_name).strip()
    
    # Remove "County" suffix if present
    county_str = re.sub(r'\s+County\s*$', '', county_str, flags=re.IGNORECASE)
    
    # Remove state suffix if present (e.g., "County, AL" or ", AL")
    county_str = re.sub(r',\s*[A-Z]{2}\s*$', '', county_str)
    
    # Remove extra whitespace
    county_str = ' '.join(county_str.split())
    
    # Title case for consistency
    county_str = county_str.title()
    
    return county_str if county_str else None


def parse_period_to_date(period: str) -> Optional[pd.Timestamp]:
    """
    Parse period string to pandas Timestamp.
    Handles formats like "24-Jul", "2024-07", "Jul-2024", etc.
    
    Args:
        period: Period string in various formats
        
    Returns:
        pandas Timestamp, or None if parsing fails
    """
    if not period or pd.isna(period):
        return None
    
    period_str = str(period).strip()
    
    # Try parsing "YY-MMM" format (e.g., "24-Jul")
    try:
        # Match pattern like "24-Jul" or "2024-Jul"
        match = re.match(r'(\d{2,4})-([A-Za-z]{3})', period_str)
        if match:
            year_str = match.group(1)
            month_str = match.group(2)
            
            # Convert 2-digit year to 4-digit (assuming 2000s)
            if len(year_str) == 2:
                year = 2000 + int(year_str)
            else:
                year = int(year_str)
            
            # Convert month abbreviation to number
            month_map = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }
            month = month_map.get(month_str.lower())
            
            if month:
                return pd.Timestamp(year=year, month=month, day=1)
    except (ValueError, AttributeError):
        pass
    
    # Try parsing "YYYY-MM" format
    try:
        match = re.match(r'(\d{4})-(\d{1,2})', period_str)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            if 1 <= month <= 12:
                return pd.Timestamp(year=year, month=month, day=1)
    except (ValueError, AttributeError):
        pass
    
    # Try parsing "MMM-YYYY" format
    try:
        match = re.match(r'([A-Za-z]{3})-(\d{2,4})', period_str)
        if match:
            month_str = match.group(1)
            year_str = match.group(2)
            
            month_map = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }
            month = month_map.get(month_str.lower())
            
            if len(year_str) == 2:
                year = 2000 + int(year_str)
            else:
                year = int(year_str)
            
            if month:
                return pd.Timestamp(year=year, month=month, day=1)
    except (ValueError, AttributeError):
        pass
    
    # Try pandas to_datetime as fallback
    try:
        return pd.to_datetime(period_str, errors='coerce')
    except (ValueError, TypeError):
        return None

