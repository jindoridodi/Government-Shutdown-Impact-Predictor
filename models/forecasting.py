"""
Forecasting functions for time series risk prediction.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai.foundation_models import TSModelInference
from ibm_watsonx_ai.foundation_models.schema import TSForecastParameters
from utils.config import API_KEY, PROJECT_ID
from utils.geocode import get_county_coordinates
from utils.logger import logger
from models.constants import MIN_DATA_POINTS, FORECAST_FREQUENCY


def augment_time_series(county_ts: pd.DataFrame, min_points: int) -> pd.DataFrame:
    """Augment time series data to meet minimum data point requirement."""
    if len(county_ts) >= min_points:
        return county_ts
    
    earliest_date = county_ts['date'].min()
    date_range = pd.date_range(
        end=earliest_date,
        periods=min_points,
        freq='M'
    )
    
    augmented_ts = pd.DataFrame({
        'date': date_range,
        'risk_index': np.nan
    })
    
    county_ts_renamed = county_ts.rename(columns={'risk_index': 'risk_index_known'})
    augmented_ts = augmented_ts.merge(
        county_ts_renamed[['date', 'risk_index_known']],
        on='date',
        how='left'
    )
    
    augmented_ts['risk_index'] = augmented_ts['risk_index_known'].fillna(augmented_ts['risk_index'])
    augmented_ts = augmented_ts[['date', 'risk_index']]
    augmented_ts = augmented_ts.sort_values('date').reset_index(drop=True)
    
    # Interpolate missing values
    augmented_ts['risk_index'] = augmented_ts['risk_index'].interpolate(
        method='linear', limit_direction='both', axis=0
    )
    augmented_ts['risk_index'] = augmented_ts['risk_index'].ffill().bfill()
    
    # Fallback to mean if still NaN
    if augmented_ts['risk_index'].isna().any():
        original_mean = county_ts_renamed['risk_index_known'].mean()
        if pd.isna(original_mean):
            original_mean = 0.0
        augmented_ts['risk_index'] = augmented_ts['risk_index'].fillna(original_mean)
    
    return augmented_ts


def prepare_county_time_series(county_data: pd.DataFrame, min_points: int) -> Optional[pd.DataFrame]:
    """Prepare and validate county time series data for forecasting."""
    county_ts = county_data[['date', 'risk_index']].copy()
    county_ts = county_ts.sort_values('date').reset_index(drop=True)
    
    # Remove NaN values
    county_ts = county_ts.dropna(subset=['risk_index'])
    
    # Handle date conversion
    if not pd.api.types.is_datetime64_any_dtype(county_ts['date']):
        county_ts['date'] = pd.to_datetime(county_ts['date'], errors='coerce')
    else:
        county_ts = county_ts[county_ts['date'].notna()].copy()
    
    county_ts = county_ts.dropna(subset=['date'])
    
    if len(county_ts) == 0:
        return None
    
    # Augment if needed
    if len(county_ts) < min_points:
        county_ts = augment_time_series(county_ts, min_points)
    
    # Truncate if too long
    if len(county_ts) > min_points:
        county_ts = county_ts.tail(min_points).reset_index(drop=True)
    
    # Final validation
    if len(county_ts) < min_points:
        return None
    
    # Convert for JSON serialization
    county_ts['date'] = county_ts['date'].dt.strftime('%Y-%m-%d')
    county_ts['risk_index'] = county_ts['risk_index'].astype(float)
    
    return county_ts


def extract_forecast_value(forecast_result: Dict[str, Any], county: str, state: str) -> Optional[float]:
    """Extract forecasted value from IBM Time Series Forecasting result."""
    if not forecast_result or "results" not in forecast_result or len(forecast_result["results"]) == 0:
        return None
    
    forecast_df = pd.DataFrame(forecast_result["results"][0])
    
    if 'risk_index' in forecast_df.columns:
        return forecast_df['risk_index'].iloc[-1]
    
    # Try to find forecast column
    forecast_cols = [col for col in forecast_df.columns if col not in ['date', 'timestamp']]
    if forecast_cols:
        return forecast_df[forecast_cols[0]].iloc[-1]
    
    logger.error(f"Could not extract forecasted value for {county}, {state}.")
    return None


def forecast_single_county(
    county: str,
    state: str,
    county_data: pd.DataFrame,
    ts_model: TSModelInference,
    min_points: int,
    idx: int
) -> Optional[Dict[str, Any]]:
    """Forecast risk for a single county."""
    # Prepare time series
    county_ts = prepare_county_time_series(county_data, min_points)
    if county_ts is None:
        if idx < 10 or (idx + 1) % 100 == 0:
            logger.warning(f"Insufficient data for {county}, {state}. Skipping.")
        return None
    
    # Diagnostic logging for first few counties
    if idx < 5:
        logger.info(f"Processing {county}, {state}: {len(county_ts)} data points")
    
    try:
        params = TSForecastParameters(
            timestamp_column="date",
            freq=FORECAST_FREQUENCY,
            target_columns=["risk_index"]
        )
        
        forecast_result = ts_model.forecast(data=county_ts, params=params)
        forecasted_value = extract_forecast_value(forecast_result, county, state)
        
        if forecasted_value is None:
            return None
        
        # Get most recent actual value
        original_data = county_data[['date', 'risk_index']].copy()
        original_data = original_data.sort_values('date')
        most_recent_actual = original_data['risk_index'].iloc[-1]
        
        # Use maximum to avoid underestimating risk
        predicted_risk = max(forecasted_value, most_recent_actual)
        
        if idx < 5:
            logger.info(f"Forecast for {county}, {state}: forecasted={forecasted_value:.6f}, actual={most_recent_actual:.6f}, combined={predicted_risk:.6f}")
        
        # Get coordinates
        lat, lon = get_county_coordinates(county, state)
        
        return {
            'region': f"{county.title()}, {state}",
            'county': county,
            'state': state,
            'risk_score': float(predicted_risk),
            'lat': lat,
            'lon': lon
        }
        
    except Exception as e:
        logger.error(f"IBM Time Series Forecasting failed for {county}, {state}: {e}")
        return None


def forecast_risk_by_county(data: pd.DataFrame, client: APIClient, forecast_horizon: int = 3) -> pd.DataFrame:
    """
    Forecasts risk for each county using IBM watsonx.ai Granite Time Series model.
    
    Args:
        data: Preprocessed time series data
        client: Initialized watsonx.ai client
        forecast_horizon: Number of periods to forecast (default: 3)
    
    Returns:
        DataFrame with county, state, predicted risk_score, lat, lon
    """
    logger.info("Starting time series forecasting for each county using IBM Time Series Forecasting...")
    
    if not API_KEY or not PROJECT_ID:
        error_msg = "API_KEY and PROJECT_ID must be set in .env file to use IBM Time Series Forecasting."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if client is None:
        error_msg = "watsonx.ai client is not initialized."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Initialize model
    # Use getattr with a fallback string identifier to avoid static attribute access errors
    model_id = getattr(client.foundation_models.TimeSeriesModels, "GRANITE_TTM_512_96_R2", None)
    if model_id is None:
        # Fallback to string identifier if the SDK does not expose the attribute
        model_id = "GRANITE_TTM_512_96_R2"
        logger.debug("TimeSeriesModels constant not found on client; using string identifier fallback for model_id.")
    ts_model = TSModelInference(model_id=model_id, api_client=client)
    
    logger.info(f"Using model {model_id} which requires at least {MIN_DATA_POINTS} data points per county")
    
    # Process each county
    counties = data[['county', 'state']].drop_duplicates()
    total_counties = len(counties)
    results = []
    
    for idx, (_, county_row) in enumerate(counties.iterrows()):
        county = county_row['county']
        state = county_row['state']
        
        county_data = data[(data['county'] == county) & (data['state'] == state)].copy()
        if len(county_data) == 0:
            continue
        
        result = forecast_single_county(county, state, county_data, ts_model, MIN_DATA_POINTS, idx)
        if result:
            results.append(result)
        
        if (idx + 1) % 10 == 0:
            logger.info(f"Processed {idx + 1}/{total_counties} counties...")
    
    if len(results) == 0:
        error_msg = "No risk scores were generated. IBM Time Series Forecasting must be available and working."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info(f"Forecasting completed for {len(results)} counties using IBM Time Series Forecasting.")
    return pd.DataFrame(results)

