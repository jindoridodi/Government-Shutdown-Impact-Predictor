"""
AI-Driven Regional Risk Forecasting using IBM watsonx.ai Granite Time Series Model
Main orchestrator script that coordinates data preprocessing and forecasting.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
from utils.data_processing import preprocess_data
from models.forecasting import forecast_risk_by_county
from models.watsonx_ts_client import initialize_client
from utils.logger import logger


def save_results(results: pd.DataFrame, output_dir: Optional[Path] = None) -> Path:
    """Save forecast results to CSV file for heatmap visualization."""
    if output_dir is None:
        repo_root = Path(__file__).resolve().parents[1]
        output_dir = repo_root / 'data' / 'processed'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'regional_risk.csv'
    
    logger.info(f"Saving forecast results to {output_path}...")
    results.to_csv(output_path, index=False)
    logger.info(f"Forecast results saved. Total counties: {len(results)}")
    return output_path


# ------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------
if __name__ == "__main__":
    try:
        print("Starting risk prediction pipeline...")
        
        print("Step 1: Preprocessing data from CSV files...")
        data = preprocess_data()
        print(f"  ✓ Loaded time series data for {data[['county', 'state']].drop_duplicates().shape[0]} counties")
        
        print("Step 2: Initializing watsonx.ai client for IBM Time Series Forecasting...")
        client = initialize_client()
        print("  ✓ Client initialized")
        
        print("Step 3: Forecasting risk for each county using IBM Time Series Forecasting...")
        forecast_results = forecast_risk_by_county(data, client, forecast_horizon=3)
        print(f"  ✓ Forecasted risk for {len(forecast_results)} counties")
        
        print("Step 4: Saving results...")
        output_path = save_results(forecast_results)
        print(f"  ✓ Results saved to {output_path}")
        
        print("\nForecast completed successfully!")
        print(f"Results are ready for heatmap visualization at: {output_path}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        print(f"Error occurred: {str(e)}")
        print("Check predictor.log for details.")
