"""
AI-Driven Regional Risk Forecasting using IBM watsonx.ai Granite Time Series Model
This script preprocesses socioeconomic datasets and forecasts regional economic risk
using IBM watsonx.ai Time Series Foundation Models (Granite TinyTimeMixers).
"""

import pandas as pd
import requests
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from io import StringIO
from datetime import datetime
import numpy as np
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai.foundation_models import TSModelInference
from ibm_watsonx_ai.foundation_models.schema import TSForecastParameters

# Load environment variables from .env file (wrap in try/except to avoid
# failing when .env contains bytes not decodable with utf-8)
env_loaded = False
try:
    env_loaded = load_dotenv()
    if env_loaded:
        print("✓ Loaded .env file")
except UnicodeDecodeError as ude:
    print(f"⚠ Warning: Failed to load .env with utf-8 decoding: {ude}. Checking environment variables.")
except Exception as e:
    # Non-fatal: dotenv is optional, don't stop execution here
    print(f"ℹ No .env file found or error loading it: {e}. Checking environment variables instead.")

# ------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------
# Reset log file on each run (filemode='w' truncates the file)
logging.basicConfig(filename='predictor.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s',
                    filemode='w')

# Log where .env was loaded from
if env_loaded:
    logging.info("Successfully loaded .env file")
else:
    logging.info("No .env file found, checking environment variables")

# ------------------------------------------------------------
# IBM watsonx.ai Configuration (loaded from .env file or environment variables)
# ------------------------------------------------------------
PROJECT_ID = os.getenv("PROJECT_ID")
API_KEY = os.getenv("API_KEY")
ENDPOINT = os.getenv("ENDPOINT", "https://us-south.ml.cloud.ibm.com")

# Log where credentials are being loaded from (without exposing actual values)
if PROJECT_ID and API_KEY:
    source = ".env file" if env_loaded else "environment variables"
    logging.info(f"Credentials loaded from {source}: PROJECT_ID={'*' * min(len(str(PROJECT_ID)), 8)}..., API_KEY={'*' * min(len(str(API_KEY)), 8)}...")
    print(f"✓ Credentials loaded from {source}")
else:
    logging.warning("Credentials not found in .env file or environment variables")
    print("⚠ Warning: API_KEY or PROJECT_ID not found in .env file or environment variables")

# Generate IAM token
def get_iam_token(api_key):
    url = "https://iam.cloud.ibm.com/identity/token"
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=data, headers=headers)
    response.raise_for_status()
    token = response.json()["access_token"]
    return token

# Initialize IBM watsonx.ai client
def initialize_client():
    logging.info("Initializing watsonx.ai client...")
    
    # Debug: Check if values are loaded (without logging the actual keys)
    api_key_loaded = API_KEY is not None and API_KEY != ""
    project_id_loaded = PROJECT_ID is not None and PROJECT_ID != ""
    
    logging.info(f"API_KEY loaded: {api_key_loaded}, PROJECT_ID loaded: {project_id_loaded}")
    
    if not API_KEY or not PROJECT_ID:
        error_msg = f"API_KEY and PROJECT_ID must be set in .env file or environment variables. API_KEY loaded: {api_key_loaded}, PROJECT_ID loaded: {project_id_loaded}"
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    # Create credentials dictionary for APIClient
    # The credentials parameter expects a dict with 'apikey' and optionally 'url'
    credentials = {
        'apikey': API_KEY,
        'url': ENDPOINT
    }
    
    # Initialize APIClient with credentials
    client = APIClient(credentials=credentials, project_id=PROJECT_ID)
    logging.info("watsonx.ai client initialized successfully.")
    return client

# ------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------
def _read_csv_flexible(path):
    """Robust CSV reader that tries common encodings."""
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]
    last_exc = None
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except UnicodeDecodeError as e:
            last_exc = e
            continue
        except Exception as e:
            raise

    # Final fallback: read bytes and decode with replacement
    try:
        with open(path, 'rb') as f:
            raw = f.read()
        text = raw.decode('utf-8', errors='replace')
        return pd.read_csv(StringIO(text), low_memory=False)
    except Exception:
        if last_exc:
            raise last_exc
        raise

def _clean_numeric_column(series):
    """Clean numeric columns that may contain commas or other formatting."""
    if series.dtype == 'object':
        return pd.to_numeric(series.astype(str).str.replace(',', '').str.replace('$', '').str.strip(), errors='coerce')
    return pd.to_numeric(series, errors='coerce')

def _normalize_county_name(county_name):
    """Normalize county names for matching."""
    if pd.isna(county_name):
        return None
    name = str(county_name).strip()
    # Remove "County" suffix and state abbreviations
    name = name.replace(' County', '').replace(' county', '').strip()
    # Remove state abbreviation at the end (e.g., "Autauga County, AL" -> "Autauga")
    if ', ' in name:
        name = name.split(',')[0].strip()
    return name.lower()

def _normalize_state_name(state_name):
    """Normalize state names to 2-letter codes."""
    if pd.isna(state_name):
        return None
    state_str = str(state_name).strip().upper()
    
    # State name to code mapping
    state_map = {
        'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR', 'CALIFORNIA': 'CA',
        'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE', 'FLORIDA': 'FL', 'GEORGIA': 'GA',
        'HAWAII': 'HI', 'IDAHO': 'ID', 'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA',
        'KANSAS': 'KS', 'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
        'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS', 'MISSOURI': 'MO',
        'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV', 'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ',
        'NEW MEXICO': 'NM', 'NEW YORK': 'NY', 'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH',
        'OKLAHOMA': 'OK', 'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
        'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT', 'VERMONT': 'VT',
        'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV', 'WISCONSIN': 'WI', 'WYOMING': 'WY',
        'DISTRICT OF COLUMBIA': 'DC', 'DC': 'DC'
    }
    
    # If already a 2-letter code, return it
    if len(state_str) == 2:
        return state_str
    
    # Map full name to code
    return state_map.get(state_str, state_str)

def _get_county_coordinates(county_name, state_name):
    """
    Get approximate coordinates for a county using a simple lookup.
    For production, consider using a geocoding service or FIPS-based lookup.
    This is a simplified version - you may want to use a proper geocoding library.
    """
    # Simple fallback: return approximate center of state
    # In production, use a proper geocoding service or FIPS lookup table
    state_centers = {
        'AL': (32.806671, -86.791130), 'AK': (61.370716, -152.404419), 'AZ': (33.729759, -111.431221),
        'AR': (34.969704, -92.373123), 'CA': (36.116203, -119.681564), 'CO': (39.059811, -105.311104),
        'CT': (41.597782, -72.755371), 'DE': (39.318523, -75.507141), 'FL': (27.766279, -81.686783),
        'GA': (33.040619, -83.643074), 'HI': (21.094318, -157.498337), 'ID': (44.240459, -114.478828),
        'IL': (40.349457, -88.986137), 'IN': (39.849426, -86.258278), 'IA': (42.011539, -93.210526),
        'KS': (38.526600, -96.726486), 'KY': (37.668140, -84.670067), 'LA': (31.169546, -91.867805),
        'ME': (44.323535, -69.765261), 'MD': (39.063946, -76.802101), 'MA': (42.230171, -71.530106),
        'MI': (43.326618, -84.536095), 'MN': (45.694454, -93.900192), 'MS': (32.741646, -89.678696),
        'MO': (38.572954, -92.189283), 'MT': (46.921925, -110.454353), 'NE': (41.125370, -98.268082),
        'NV': (38.313515, -117.055374), 'NH': (43.452492, -71.563896), 'NJ': (40.298904, -74.521011),
        'NM': (34.840515, -106.248482), 'NY': (42.165726, -74.948051), 'NC': (35.630066, -79.806419),
        'ND': (47.528912, -99.784012), 'OH': (40.388783, -82.764915), 'OK': (35.565342, -96.928917),
        'OR': (44.572021, -122.070938), 'PA': (40.590752, -77.209755), 'RI': (41.680893, -71.51178),
        'SC': (33.856892, -80.945007), 'SD': (44.299782, -99.438828), 'TN': (35.747845, -86.692345),
        'TX': (31.054487, -97.563461), 'UT': (40.150032, -111.862434), 'VT': (44.045876, -72.710686),
        'VA': (37.769337, -78.169968), 'WA': (47.400902, -121.490494), 'WV': (38.491226, -80.954453),
        'WI': (44.268543, -89.616508), 'WY': (42.755966, -107.302490), 'DC': (38.907192, -77.036873)
    }
    
    state_code = _normalize_state_name(state_name)
    if state_code in state_centers:
        return state_centers[state_code]
    # Default to center of US
    return (39.8283, -98.5795)

# ------------------------------------------------------------
# Data Preprocessing
# ------------------------------------------------------------
def preprocess_data():
    """
    Load and merge all datasets to compute a composite socioeconomic index per county.
    Creates time series data for forecasting.
    """
    logging.info("Starting data preprocessing...")

    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / 'data'

    # Load CSV files with correct names
    logging.info("Loading CSV files...")
    federal_df = _read_csv_flexible(data_dir / "federalEmploymentByCounty.csv")
    snap_df = _read_csv_flexible(data_dir / "snapParticipationByCounty.csv")
    unemployment_df = _read_csv_flexible(data_dir / "unemploymentByCounty.csv")
    cost_df = _read_csv_flexible(data_dir / "costOfLivingByCounty.csv")

    logging.info(f"Loaded {len(federal_df)} federal employment records")
    logging.info(f"Loaded {len(snap_df)} SNAP records")
    logging.info(f"Loaded {len(unemployment_df)} unemployment records")
    logging.info(f"Loaded {len(cost_df)} cost of living records")

    # Process Federal Employment data
    logging.info("Processing Federal Employment data...")
    federal_df.columns = federal_df.columns.str.strip()
    # Extract monthly employment (January, February, March)
    federal_processed = []
    for _, row in federal_df.iterrows():
        county = str(row.get('County', '')).strip()
        state = str(row.get('State', '')).strip()
        year = row.get('Year', 2025)
        
        # Get employment values
        jan_emp = _clean_numeric_column(pd.Series([row.get('January Employment', 0)]))[0] or 0
        feb_emp = _clean_numeric_column(pd.Series([row.get('February Employment', 0)]))[0] or 0
        mar_emp = _clean_numeric_column(pd.Series([row.get('March Employment', 0)]))[0] or 0
        
        # Create monthly records
        for month, emp in [('01', jan_emp), ('02', feb_emp), ('03', mar_emp)]:
            federal_processed.append({
                'county': _normalize_county_name(county),
                'state': _normalize_state_name(state),
                'year': year,
                'month': month,
                'date': pd.to_datetime(f"{year}-{month}-01", errors='coerce'),
                'federal_employment': emp
            })
    
    federal_ts = pd.DataFrame(federal_processed)
    federal_ts = federal_ts.dropna(subset=['date', 'county', 'state'])

    # Process Unemployment data
    logging.info("Processing Unemployment data...")
    unemployment_df.columns = unemployment_df.columns.str.strip()
    
    # FIPS to state code mapping (first 2 digits of FIPS)
    fips_to_state = {
        '01': 'AL', '02': 'AK', '04': 'AZ', '05': 'AR', '06': 'CA', '08': 'CO', '09': 'CT',
        '10': 'DE', '11': 'DC', '12': 'FL', '13': 'GA', '15': 'HI', '16': 'ID', '17': 'IL',
        '18': 'IN', '19': 'IA', '20': 'KS', '21': 'KY', '22': 'LA', '23': 'ME', '24': 'MD',
        '25': 'MA', '26': 'MI', '27': 'MN', '28': 'MS', '29': 'MO', '30': 'MT', '31': 'NE',
        '32': 'NV', '33': 'NH', '34': 'NJ', '35': 'NM', '36': 'NY', '37': 'NC', '38': 'ND',
        '39': 'OH', '40': 'OK', '41': 'OR', '42': 'PA', '44': 'RI', '45': 'SC', '46': 'SD',
        '47': 'TN', '48': 'TX', '49': 'UT', '50': 'VT', '51': 'VA', '53': 'WA', '54': 'WV',
        '55': 'WI', '56': 'WY'
    }
    
    unemployment_processed = []
    for _, row in unemployment_df.iterrows():
        county_full = str(row.get('County', ''))
        county = _normalize_county_name(county_full)
        state_fips = str(row.get('State FIPS Code', '')).zfill(2)
        state_code = fips_to_state.get(state_fips, state_fips)  # Convert FIPS to state code
        period = str(row.get('Period', ''))
        unemp_rate = _clean_numeric_column(pd.Series([row.get('Unemploy-ment Rate (%)', row.get('Unemployment Rate (%)', 0))]))[0] or 0
        
        # Parse period (e.g., "24-Jul" -> 2024-07)
        try:
            if '-' in period:
                year_part, month_name = period.split('-')
                year = 2000 + int(year_part) if len(year_part) == 2 else int(year_part)
                month_num = datetime.strptime(month_name, '%b').month
                date = pd.to_datetime(f"{year}-{month_num:02d}-01", errors='coerce')
            else:
                date = pd.to_datetime(period, errors='coerce')
        except:
            date = pd.NaT
        
        if pd.notna(date) and county:
            unemployment_processed.append({
                'county': county,
                'state': state_code,
                'date': date,
                'unemployment_rate': unemp_rate
            })
    
    unemployment_ts = pd.DataFrame(unemployment_processed)
    unemployment_ts = unemployment_ts.dropna(subset=['date', 'county'])

    # Process SNAP data (aggregate to monthly, use latest available)
    logging.info("Processing SNAP data...")
    snap_df.columns = snap_df.columns.str.strip()
    snap_processed = []
    for _, row in snap_df.iterrows():
        county = _normalize_county_name(str(row.get('county_name', '')))
        state = _normalize_state_name(str(row.get('state_name', '')))
        snap_households = _clean_numeric_column(pd.Series([row.get('snap_households', 0)]))[0] or 0
        
        if county and state:
            snap_processed.append({
                'county': county,
                'state': state,
                'snap_households': snap_households
            })
    
    snap_latest = pd.DataFrame(snap_processed)

    # Process Cost of Living data (aggregate, use latest)
    logging.info("Processing Cost of Living data...")
    cost_df.columns = cost_df.columns.str.strip()
    cost_processed = []
    for _, row in cost_df.iterrows():
        county = _normalize_county_name(str(row.get('county', '')))
        state = _normalize_state_name(str(row.get('state', '')))
        total_cost = _clean_numeric_column(pd.Series([row.get('total_cost', 0)]))[0] or 0
        
        if county and state:
            cost_processed.append({
                'county': county,
                'state': state,
                'total_cost': total_cost
            })
    
    cost_latest = pd.DataFrame(cost_processed)

    # Merge time series data
    logging.info("Merging time series data...")
    # Use unemployment as base since it has more time periods (14 months vs 3 months for federal)
    # This gives us more data points per county for better forecasting
    merged_ts = unemployment_ts.copy()
    
    # Merge federal employment (has time dimension but fewer periods)
    merged_ts = merged_ts.merge(
        federal_ts[['county', 'state', 'date', 'federal_employment']],
        on=['county', 'state', 'date'],
        how='left'
    )
    
    # Merge SNAP and Cost (static for now, use latest values)
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
    logging.info("Calculating risk index...")
    # Fill missing values with safe defaults
    merged_ts['federal_employment'] = merged_ts['federal_employment'].fillna(0)
    
    # Handle unemployment_rate - use median if available, otherwise use 0
    unemp_median = merged_ts['unemployment_rate'].median()
    if pd.isna(unemp_median):
        unemp_median = 0
    merged_ts['unemployment_rate'] = merged_ts['unemployment_rate'].fillna(unemp_median)
    
    merged_ts['snap_households'] = merged_ts['snap_households'].fillna(0)
    
    # Handle total_cost - use median if available, otherwise use 0
    cost_median = merged_ts['total_cost'].median()
    if pd.isna(cost_median):
        cost_median = 0
    merged_ts['total_cost'] = merged_ts['total_cost'].fillna(cost_median)
    
    # Estimate population from available data (simplified)
    # In production, you'd have actual population data
    merged_ts['population'] = merged_ts['federal_employment'] * 50  # Rough estimate
    merged_ts['population'] = merged_ts['population'].fillna(0)  # Ensure no NaN
    
    # Calculate normalized features with safe division
    merged_ts['employment_ratio'] = merged_ts['federal_employment'] / (merged_ts['population'] + 1)
    merged_ts['snap_rate'] = merged_ts['snap_households'] / (merged_ts['population'] + 1)
    merged_ts['unemployment_rate_norm'] = merged_ts['unemployment_rate'] / 100
    
    # Normalize cost_index - handle case where all values are the same
    cost_min = merged_ts['total_cost'].min()
    cost_max = merged_ts['total_cost'].max()
    cost_range = cost_max - cost_min
    if cost_range == 0 or pd.isna(cost_range):
        # All values are the same or invalid, set to 0
        merged_ts['cost_index_norm'] = 0.0
    else:
        merged_ts['cost_index_norm'] = (merged_ts['total_cost'] - cost_min) / cost_range
    
    # Ensure all intermediate values are finite (no NaN or inf)
    merged_ts['employment_ratio'] = merged_ts['employment_ratio'].replace([np.inf, -np.inf], 0).fillna(0)
    merged_ts['snap_rate'] = merged_ts['snap_rate'].replace([np.inf, -np.inf], 0).fillna(0)
    merged_ts['unemployment_rate_norm'] = merged_ts['unemployment_rate_norm'].replace([np.inf, -np.inf], 0).fillna(0)
    merged_ts['cost_index_norm'] = merged_ts['cost_index_norm'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # Composite risk index
    merged_ts['risk_index'] = (
        0.4 * merged_ts['employment_ratio'] +
        0.3 * merged_ts['unemployment_rate_norm'] +
        0.2 * merged_ts['snap_rate'] +
        0.1 * merged_ts['cost_index_norm']
    )
    
    # Final safety check - replace any remaining NaN or inf with 0
    merged_ts['risk_index'] = merged_ts['risk_index'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # Log statistics about risk_index
    risk_nan_count = merged_ts['risk_index'].isna().sum()
    risk_valid_count = merged_ts['risk_index'].notna().sum()
    logging.info(f"Risk index calculation: {risk_valid_count} valid values, {risk_nan_count} NaN values")
    if risk_valid_count > 0:
        logging.info(f"Risk index stats: min={merged_ts['risk_index'].min():.6f}, max={merged_ts['risk_index'].max():.6f}, mean={merged_ts['risk_index'].mean():.6f}")

    # Sort by date and county
    merged_ts = merged_ts.sort_values(['county', 'state', 'date']).reset_index(drop=True)
    
    logging.info(f"Preprocessed {len(merged_ts)} time series records for {merged_ts[['county', 'state']].drop_duplicates().shape[0]} counties")
    return merged_ts

# ------------------------------------------------------------
# Forecasting with watsonx.ai Granite Model
# ------------------------------------------------------------
def forecast_risk_by_county(data, client, forecast_horizon=3):
    """
    Forecasts risk for each county using IBM watsonx.ai Granite Time Series model ONLY.
    Returns a DataFrame with county, state, predicted risk_score, lat, lon.
    Raises an error if IBM Time Series Forecasting is not available.
    """
    logging.info("Starting time series forecasting for each county using IBM Time Series Forecasting...")
    
    if not API_KEY or not PROJECT_ID:
        error_msg = "API_KEY and PROJECT_ID must be set in .env file to use IBM Time Series Forecasting. Cannot generate risk_score without IBM Time Series Forecasting."
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    if client is None:
        error_msg = "watsonx.ai client is not initialized. Cannot generate risk_score without IBM Time Series Forecasting."
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    # Define model and parameters
    # According to IBM watsonx.ai documentation:
    # - GRANITE_TTM_512_96_R2 requires at least 512 data points per channel
    # - GRANITE_TTM_1024_96_R2 requires at least 1,024 data points per channel
    # - GRANITE_TTM_1536_96_R2 requires at least 1,536 data points per channel
    model_id = client.foundation_models.TimeSeriesModels.GRANITE_TTM_512_96_R2
    MIN_DATA_POINTS = 512  # Minimum required by the model
    
    ts_model = TSModelInference(model_id=model_id, api_client=client)
    
    results = []
    counties = data[['county', 'state']].drop_duplicates()
    total_counties = len(counties)
    
    logging.info(f"Using model {model_id} which requires at least {MIN_DATA_POINTS} data points per county")
    
    for idx, (_, county_row) in enumerate(counties.iterrows()):
        county = county_row['county']
        state = county_row['state']
        
        # Get time series for this county
        county_data = data[(data['county'] == county) & (data['state'] == state)].copy()
        
        if len(county_data) == 0:
            continue
        
        # Prepare data for forecasting
        county_ts = county_data[['date', 'risk_index']].copy()
        county_ts = county_ts.sort_values('date').reset_index(drop=True)
        
        # Remove rows with NaN values in risk_index (API cannot handle NaN in JSON)
        # According to IBM documentation: "You cannot skip a data point or specify null as the data point"
        initial_count = len(county_ts)
        county_ts = county_ts.dropna(subset=['risk_index'])
        after_risk_filter = len(county_ts)
        
        # Handle date conversion - check if it's already a datetime
        if not pd.api.types.is_datetime64_any_dtype(county_ts['date']):
            county_ts['date'] = pd.to_datetime(county_ts['date'], errors='coerce')
        else:
            # Already datetime, but ensure no NaT values
            county_ts = county_ts[county_ts['date'].notna()].copy()
        
        # Remove any rows where date is still invalid
        county_ts = county_ts.dropna(subset=['date'])
        after_date_filter = len(county_ts)
        
        # Diagnostic logging for first few counties to understand data issues
        if idx < 5:
            logging.info(f"County {county}, {state}: initial={initial_count}, after_risk_filter={after_risk_filter}, after_date_filter={after_date_filter}")
        
        # If we have fewer than MIN_DATA_POINTS, augment the data using interpolation
        # This creates a synthetic time series by extending the data backward in time
        if len(county_ts) < MIN_DATA_POINTS:
            # Calculate how many months we need to go back
            months_needed = MIN_DATA_POINTS - len(county_ts)
            
            # Get the earliest date in the data
            earliest_date = county_ts['date'].min()
            
            # Create a monthly date range going back from the earliest date
            # We'll create enough months to reach MIN_DATA_POINTS total
            date_range = pd.date_range(
                end=earliest_date,
                periods=MIN_DATA_POINTS,
                freq='M'  # Monthly frequency
            )
            
            # Create a new DataFrame with the full date range
            augmented_ts = pd.DataFrame({
                'date': date_range,
                'risk_index': np.nan
            })
            
            # Merge with existing data to fill in known values
            # Rename risk_index in county_ts to avoid conflict
            county_ts_renamed = county_ts.rename(columns={'risk_index': 'risk_index_known'})
            augmented_ts = augmented_ts.merge(
                county_ts_renamed[['date', 'risk_index_known']],
                on='date',
                how='left'
            )
            
            # Use known values where available, otherwise keep NaN for interpolation
            augmented_ts['risk_index'] = augmented_ts['risk_index_known'].fillna(augmented_ts['risk_index'])
            augmented_ts = augmented_ts[['date', 'risk_index']]
            
            # Sort by date
            augmented_ts = augmented_ts.sort_values('date').reset_index(drop=True)
            
            # Interpolate missing values using linear interpolation
            augmented_ts['risk_index'] = augmented_ts['risk_index'].interpolate(method='linear', limit_direction='both', axis=0)
            
            # Fill any remaining NaN values (at the beginning/end) using forward/backward fill
            augmented_ts['risk_index'] = augmented_ts['risk_index'].ffill().bfill()
            
            # If still NaN (shouldn't happen, but safety check), use the mean of original data
            if augmented_ts['risk_index'].isna().any():
                # Get mean from the original county_ts data (before augmentation)
                original_mean = county_ts_renamed['risk_index_known'].mean()
                if pd.isna(original_mean):
                    original_mean = 0.0  # Fallback to 0 if all values were NaN
                augmented_ts['risk_index'] = augmented_ts['risk_index'].fillna(original_mean)
            
            county_ts = augmented_ts
            
            if idx < 5:
                logging.info(f"Augmented {county}, {state}: expanded from {after_date_filter} to {len(county_ts)} data points")
        
        # Ensure we have exactly MIN_DATA_POINTS (take the most recent if we have more)
        if len(county_ts) > MIN_DATA_POINTS:
            county_ts = county_ts.tail(MIN_DATA_POINTS).reset_index(drop=True)
        
        # Final check - should never happen now, but safety check
        if len(county_ts) < MIN_DATA_POINTS:
            if idx < 10 or (idx + 1) % 100 == 0:
                logging.warning(f"Still insufficient data for {county}, {state}: {len(county_ts)} points (requires {MIN_DATA_POINTS}). Skipping.")
            continue
        
        # Convert Timestamp objects to strings for JSON serialization
        # According to IBM documentation, ISO 8601 format is recommended
        # For monthly data, we use YYYY-MM-DD format
        county_ts['date'] = county_ts['date'].dt.strftime('%Y-%m-%d')
        
        # Ensure risk_index is a native Python float (not numpy float) for proper JSON serialization
        # This ensures the values are JSON-serializable native Python types
        county_ts['risk_index'] = county_ts['risk_index'].astype(float)
        
        # If we have more than MIN_DATA_POINTS, use only the most recent MIN_DATA_POINTS
        # According to documentation: "If you specify more than the required number, 
        # the model uses the most recent data points up to the model requirement"
        if len(county_ts) > MIN_DATA_POINTS:
            county_ts = county_ts.tail(MIN_DATA_POINTS).reset_index(drop=True)
        
        try:
            # Create TSForecastParameters with required fields
            # According to IBM watsonx.ai documentation:
            # - timestamp_column: name of the date/time column
            # - freq: frequency string (e.g., "M" for monthly, "1h" for hourly)
            # - target_columns: list of columns to forecast
            params = TSForecastParameters(
                timestamp_column="date",
                freq="M",  # monthly frequency (M = month end frequency)
                target_columns=["risk_index"]
            )
            
            # Forecast future values using IBM Time Series Forecasting
            # According to documentation: forecast(data, params=None, future_data=None)
            # The data must have serializable types (strings, not Timestamps)
            forecast_result = ts_model.forecast(data=county_ts, params=params)
            
            # Extract forecasted values from IBM Time Series Forecasting
            if forecast_result and "results" in forecast_result and len(forecast_result["results"]) > 0:
                forecast_df = pd.DataFrame(forecast_result["results"][0])
                
                # Get the forecasted value
                if 'risk_index' in forecast_df.columns:
                    forecasted_value = forecast_df['risk_index'].iloc[-1]
                else:
                    # If column name is different, try to find the forecast column
                    forecast_cols = [col for col in forecast_df.columns if col != 'date' and col != 'timestamp']
                    if forecast_cols:
                        forecasted_value = forecast_df[forecast_cols[0]].iloc[-1]
                    else:
                        logging.error(f"Could not extract forecasted value for {county}, {state}. Skipping.")
                        continue
                
                # Get the most recent actual risk_index value from the original data (before augmentation)
                # This preserves the actual observed risk rather than relying solely on forecasted values
                # which may be smoothed by the interpolation
                original_data = county_data[['date', 'risk_index']].copy()
                original_data = original_data.sort_values('date')
                most_recent_actual = original_data['risk_index'].iloc[-1]
                
                # Use the maximum of forecasted and recent actual to avoid underestimating risk
                # This ensures we don't miss high-risk counties due to smoothing from interpolation
                predicted_risk = max(forecasted_value, most_recent_actual)
                
                # Alternative: Use a weighted combination (uncomment to use instead)
                # predicted_risk = 0.7 * forecasted_value + 0.3 * most_recent_actual
                
                if idx < 5:
                    logging.info(f"Forecast for {county}, {state}: forecasted={forecasted_value:.6f}, actual={most_recent_actual:.6f}, combined={predicted_risk:.6f}")
            else:
                error_msg = f"IBM Time Series Forecasting returned no results for {county}, {state}. Cannot generate risk_score."
                logging.error(error_msg)
                continue
                
        except Exception as e:
            error_msg = f"IBM Time Series Forecasting failed for {county}, {state}: {e}. Cannot generate risk_score."
            logging.error(error_msg)
            continue
        
        # Get coordinates
        lat, lon = _get_county_coordinates(county, state)
        
        results.append({
            'region': f"{county.title()}, {state}",
            'county': county,
            'state': state,
            'risk_score': float(predicted_risk),
            'lat': lat,
            'lon': lon
        })
        
        if (idx + 1) % 10 == 0:
            logging.info(f"Processed {idx + 1}/{total_counties} counties...")
    
    if len(results) == 0:
        error_msg = "No risk scores were generated. IBM Time Series Forecasting must be available and working to generate risk_score."
        logging.error(error_msg)
        raise RuntimeError(error_msg)
    
    logging.info(f"Forecasting completed for {len(results)} counties using IBM Time Series Forecasting.")
    return pd.DataFrame(results)


# ------------------------------------------------------------
# Save Results
# ------------------------------------------------------------
def save_results(results, output_dir=None):
    """Save forecast results to CSV file for heatmap visualization."""
    if output_dir is None:
        repo_root = Path(__file__).resolve().parents[1]
        output_dir = repo_root / 'data' / 'processed'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'regional_risk.csv'
    
    logging.info(f"Saving forecast results to {output_path}...")
    results.to_csv(output_path, index=False)
    logging.info(f"Forecast results saved. Total counties: {len(results)}")
    return output_path

# ------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------
if __name__ == "__main__":
    try:
        print("Starting risk prediction pipeline...")
        
        # Preprocess data
        print("Step 1: Preprocessing data from CSV files...")
        data = preprocess_data()
        print(f"  ✓ Loaded time series data for {data[['county', 'state']].drop_duplicates().shape[0]} counties")
        
        # Initialize client (required for IBM Time Series Forecasting)
        print("Step 2: Initializing watsonx.ai client for IBM Time Series Forecasting...")
        client = initialize_client()
        print("  ✓ Client initialized")
        
        # Forecast risk using IBM Time Series Forecasting ONLY
        print("Step 3: Forecasting risk for each county using IBM Time Series Forecasting...")
        forecast_results = forecast_risk_by_county(data, client, forecast_horizon=3)
        print(f"  ✓ Forecasted risk for {len(forecast_results)} counties")
        
        # Save results
        print("Step 4: Saving results...")
        output_path = save_results(forecast_results)
        print(f"  ✓ Results saved to {output_path}")
        
        print("\nForecast completed successfully!")
        print(f"Results are ready for heatmap visualization at: {output_path}")
        
    except Exception as e:
        logging.error(f"Error: {str(e)}", exc_info=True)
        print(f"Error occurred: {str(e)}")
        print("Check predictor.log for details.")
