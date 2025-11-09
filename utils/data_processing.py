"""
Data loading and preprocessing functions.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import sys
# Add parent directory to path to allow importing from models
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
from utils.helpers import read_csv_flexible, clean_numeric_column, normalize_county_name, parse_period_to_date
from utils.geocode import normalize_state_name
from utils.logger import logger
from models.constants import FIPS_TO_STATE, RISK_WEIGHTS, POPULATION_ESTIMATE_MULTIPLIER


def process_federal_employment(federal_df: pd.DataFrame) -> pd.DataFrame:
    """Process federal employment data into time series format."""
    logger.info("Processing Federal Employment data...")
    federal_df.columns = federal_df.columns.str.strip()
    
    federal_processed = []
    for _, row in federal_df.iterrows():
        county = str(row.get('County', '')).strip()
        state = str(row.get('State', '')).strip()
        year = row.get('Year', 2025)
        
        jan_emp = clean_numeric_column(pd.Series([row.get('January Employment', 0)]))[0] or 0
        feb_emp = clean_numeric_column(pd.Series([row.get('February Employment', 0)]))[0] or 0
        mar_emp = clean_numeric_column(pd.Series([row.get('March Employment', 0)]))[0] or 0
        
        for month, emp in [('01', jan_emp), ('02', feb_emp), ('03', mar_emp)]:
            federal_processed.append({
                'county': normalize_county_name(county),
                'state': normalize_state_name(state),
                'year': year,
                'month': month,
                'date': pd.to_datetime(f"{year}-{month}-01", errors='coerce'),
                'federal_employment': emp
            })
    
    federal_ts = pd.DataFrame(federal_processed)
    return federal_ts.dropna(subset=['date', 'county', 'state'])


def process_unemployment(unemployment_df: pd.DataFrame) -> pd.DataFrame:
    """Process unemployment data into time series format."""
    logger.info("Processing Unemployment data...")
    unemployment_df.columns = unemployment_df.columns.str.strip()
    
    unemployment_processed = []
    for _, row in unemployment_df.iterrows():
        county_full = str(row.get('County', ''))
        county = normalize_county_name(county_full)
        state_fips = str(row.get('State FIPS Code', '')).zfill(2)
        state_code = FIPS_TO_STATE.get(state_fips, state_fips)
        period = str(row.get('Period', ''))
        unemp_rate = clean_numeric_column(
            pd.Series([row.get('Unemploy-ment Rate (%)', row.get('Unemployment Rate (%)', 0))])
        )[0] or 0
        
        date = parse_period_to_date(period)
        
        if date and pd.notna(date) and county:
            unemployment_processed.append({
                'county': county,
                'state': state_code,
                'date': date,
                'unemployment_rate': unemp_rate
            })
    
    unemployment_ts = pd.DataFrame(unemployment_processed)
    return unemployment_ts.dropna(subset=['date', 'county'])


def process_snap_data(snap_df: pd.DataFrame) -> pd.DataFrame:
    """Process SNAP data into static format."""
    logger.info("Processing SNAP data...")
    snap_df.columns = snap_df.columns.str.strip()
    
    snap_processed = []
    for _, row in snap_df.iterrows():
        county = normalize_county_name(str(row.get('county_name', '')))
        state = normalize_state_name(str(row.get('state_name', '')))
        snap_households = clean_numeric_column(pd.Series([row.get('snap_households', 0)]))[0] or 0
        
        if county and state:
            snap_processed.append({
                'county': county,
                'state': state,
                'snap_households': snap_households
            })
    
    return pd.DataFrame(snap_processed)


def process_cost_data(cost_df: pd.DataFrame) -> pd.DataFrame:
    """Process cost of living data into static format."""
    logger.info("Processing Cost of Living data...")
    cost_df.columns = cost_df.columns.str.strip()
    
    cost_processed = []
    for _, row in cost_df.iterrows():
        county = normalize_county_name(str(row.get('county', '')))
        state = normalize_state_name(str(row.get('state', '')))
        total_cost = clean_numeric_column(pd.Series([row.get('total_cost', 0)]))[0] or 0
        
        if county and state:
            cost_processed.append({
                'county': county,
                'state': state,
                'total_cost': total_cost
            })
    
    return pd.DataFrame(cost_processed)


def calculate_risk_index(merged_ts: pd.DataFrame) -> pd.DataFrame:
    """Calculate composite risk index from normalized features."""
    logger.info("Calculating risk index...")
    
    # Fill missing values with safe defaults
    merged_ts['federal_employment'] = merged_ts['federal_employment'].fillna(0)
    
    unemp_median = merged_ts['unemployment_rate'].median()
    if pd.isna(unemp_median):
        unemp_median = 0
    merged_ts['unemployment_rate'] = merged_ts['unemployment_rate'].fillna(unemp_median)
    
    merged_ts['snap_households'] = merged_ts['snap_households'].fillna(0)
    
    cost_median = merged_ts['total_cost'].median()
    if pd.isna(cost_median):
        cost_median = 0
    merged_ts['total_cost'] = merged_ts['total_cost'].fillna(cost_median)
    
    # Estimate population
    merged_ts['population'] = merged_ts['federal_employment'] * POPULATION_ESTIMATE_MULTIPLIER
    merged_ts['population'] = merged_ts['population'].fillna(0)
    
    # Calculate normalized features
    merged_ts['employment_ratio'] = merged_ts['federal_employment'] / (merged_ts['population'] + 1)
    merged_ts['snap_rate'] = merged_ts['snap_households'] / (merged_ts['population'] + 1)
    merged_ts['unemployment_rate_norm'] = merged_ts['unemployment_rate'] / 100
    
    # Normalize cost_index
    cost_min = merged_ts['total_cost'].min()
    cost_max = merged_ts['total_cost'].max()
    cost_range = cost_max - cost_min
    if cost_range == 0 or pd.isna(cost_range):
        merged_ts['cost_index_norm'] = 0.0
    else:
        merged_ts['cost_index_norm'] = (merged_ts['total_cost'] - cost_min) / cost_range
    
    # Ensure all intermediate values are finite
    merged_ts['employment_ratio'] = merged_ts['employment_ratio'].replace([np.inf, -np.inf], 0).fillna(0)
    merged_ts['snap_rate'] = merged_ts['snap_rate'].replace([np.inf, -np.inf], 0).fillna(0)
    merged_ts['unemployment_rate_norm'] = merged_ts['unemployment_rate_norm'].replace([np.inf, -np.inf], 0).fillna(0)
    merged_ts['cost_index_norm'] = merged_ts['cost_index_norm'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # Composite risk index
    merged_ts['risk_index'] = (
        RISK_WEIGHTS['employment_ratio'] * merged_ts['employment_ratio'] +
        RISK_WEIGHTS['unemployment_rate'] * merged_ts['unemployment_rate_norm'] +
        RISK_WEIGHTS['snap_rate'] * merged_ts['snap_rate'] +
        RISK_WEIGHTS['cost_index'] * merged_ts['cost_index_norm']
    )
    
    # Final safety check
    merged_ts['risk_index'] = merged_ts['risk_index'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # Log statistics
    risk_nan_count = merged_ts['risk_index'].isna().sum()
    risk_valid_count = merged_ts['risk_index'].notna().sum()
    logger.info(f"Risk index calculation: {risk_valid_count} valid values, {risk_nan_count} NaN values")
    if risk_valid_count > 0:
        logger.info(f"Risk index stats: min={merged_ts['risk_index'].min():.6f}, max={merged_ts['risk_index'].max():.6f}, mean={merged_ts['risk_index'].mean():.6f}")
    
    return merged_ts


def preprocess_data() -> pd.DataFrame:
    """
    Load and merge all datasets to compute a composite socioeconomic index per county.
    Creates time series data for forecasting.
    """
    logger.info("Starting data preprocessing...")

    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / 'data'

    # Load CSV files
    logger.info("Loading CSV files...")
    federal_df = read_csv_flexible(data_dir / "federalEmploymentByCounty.csv")
    snap_df = read_csv_flexible(data_dir / "snapParticipationByCounty.csv")
    unemployment_df = read_csv_flexible(data_dir / "unemploymentByCounty.csv")
    cost_df = read_csv_flexible(data_dir / "costOfLivingByCounty.csv")

    logger.info(f"Loaded {len(federal_df)} federal employment records")
    logger.info(f"Loaded {len(snap_df)} SNAP records")
    logger.info(f"Loaded {len(unemployment_df)} unemployment records")
    logger.info(f"Loaded {len(cost_df)} cost of living records")

    # Process each dataset
    federal_ts = process_federal_employment(federal_df)
    unemployment_ts = process_unemployment(unemployment_df)
    snap_latest = process_snap_data(snap_df)
    cost_latest = process_cost_data(cost_df)

    # Merge time series data
    logger.info("Merging time series data...")
    merged_ts = unemployment_ts.copy()
    
    merged_ts = merged_ts.merge(
        federal_ts[['county', 'state', 'date', 'federal_employment']],
        on=['county', 'state', 'date'],
        how='left'
    )
    
    merged_ts = merged_ts.merge(
        snap_latest[['county', 'state', 'snap_households']],
        on=['county', 'state'],
        how='left'
    )
    
    merged_ts = merged_ts.merge(
        cost_latest[['county', 'state', 'total_cost']],
        on=['county', 'state'],
        how='left'
    )

    # Calculate risk index
    merged_ts = calculate_risk_index(merged_ts)

    # Sort by date and county
    merged_ts = merged_ts.sort_values(['county', 'state', 'date']).reset_index(drop=True)
    
    logger.info(f"Preprocessed {len(merged_ts)} time series records for {merged_ts[['county', 'state']].drop_duplicates().shape[0]} counties")
    return merged_ts

