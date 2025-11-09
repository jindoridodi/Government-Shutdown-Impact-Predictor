"""
AI-Driven Regional Risk Forecasting using IBM watsonx.ai Granite Time Series Model
This script preprocesses socioeconomic datasets and forecasts regional economic risk
using IBM watsonx.ai Time Series Foundation Models (Granite TinyTimeMixers).
"""

import pandas as pd
import requests
import logging
from pathlib import Path
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai.foundation_models import TSModelInference
from ibm_watsonx_ai.foundation_models.schema import TSForecastParameters

# ------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------
logging.basicConfig(filename='predictor.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# ------------------------------------------------------------
# IBM watsonx.ai Configuration (use your credentials)
# ------------------------------------------------------------
PROJECT_ID = "adf0626a-5f99-4f48-b3eb-2f46a450c059"
API_KEY = "MIDUEQgmSHM17CEJ0WDRZiSTjZ18eZFt8Ko66vrJQZNV"
ENDPOINT = "https://us-south.ml.cloud.ibm.com"

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
    token = get_iam_token(API_KEY)
    client = APIClient(api_key=API_KEY, project_id=PROJECT_ID, service_url=ENDPOINT)
    logging.info("watsonx.ai client initialized.")
    return client

# ------------------------------------------------------------
# Data Preprocessing
# ------------------------------------------------------------
def preprocess_data():
    """
    Load and merge all datasets to compute a composite socioeconomic index per county.
    """
    logging.info("Starting data preprocessing...")

    # Load datasets from the project's data/ directory
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / 'data'

    # Build full paths and read CSVs
    federal = pd.read_csv(data_dir / "Federal Employment.csv")
    snap = pd.read_csv(data_dir / "SNAPParticipation.csv")
    unemployment = pd.read_csv(data_dir / "unemployment.csv")
    cost = pd.read_csv(data_dir / "CostOfLiving.csv")

    # Merge on common keys (assume 'county' and 'state' columns exist)
    data = federal.merge(snap, on=["county", "state"], how="left") \
                  .merge(unemployment, on=["county", "state"], how="left") \
                  .merge(cost, on=["county", "state"], how="left")

    # Compute derived features
    data["employment_ratio"] = data["federal_employment"] / data["population"]
    data["snap_rate"] = data["snap_households"] / data["population"]
    data["unemployment_rate"] = data["unemployment_rate"] / 100
    data["cost_index_norm"] = data["cost_index"] / data["cost_index"].max()

    # Composite socioeconomic risk index
    data["risk_index"] = (
        0.4 * data["employment_ratio"] +
        0.3 * data["unemployment_rate"] +
        0.2 * data["snap_rate"] +
        0.1 * data["cost_index_norm"]
    )

    logging.info("Data preprocessing completed.")
    return data

# ------------------------------------------------------------
# Forecasting with watsonx.ai Granite Model
# ------------------------------------------------------------
def forecast_risk(data, client):
    """
    Uses IBM watsonx.ai Granite Time Series model to forecast regional risk scores.
    """
    logging.info("Starting time series forecasting...")

    # Define model and parameters
    model_id = client.foundation_models.TimeSeriesModels.GRANITE_TTM_512_96_R2
    ts_model = TSModelInference(model_id=model_id, api_client=client)

    params = TSForecastParameters(
        timestamp_column="date",
        freq="M",  # monthly frequency
        target_columns=["risk_index"]
    )

    # Prepare data (assume sorted by date)
    data = data.sort_values(by="date")

    # Forecast future values
    results = ts_model.forecast(data=data, params=params)["results"][0]

    logging.info("Forecasting completed.")
    return pd.DataFrame(results)

# ------------------------------------------------------------
# Save Results
# ------------------------------------------------------------
def save_results(results, filename="predicted_regional_risk.csv"):
    logging.info("Saving forecast results...")
    results.to_csv(filename, index=False)
    logging.info(f"Forecast results saved to {filename}.")

# ------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------
if __name__ == "__main__":
    try:
        data = preprocess_data()
        client = initialize_client()
        forecast_results = forecast_risk(data, client)
        save_results(forecast_results)
        print("Forecast completed successfully. Results saved.")
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        print(f"Error occurred: {str(e)}")
