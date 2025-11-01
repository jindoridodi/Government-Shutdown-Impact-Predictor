
# analytics.py

import pandas as pd
import numpy as np
from statsmodels.formula.api import ols
import logging

# Configure logging
logging.basicConfig(filename='analytics.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

def calculate_scores(df):
    """
    Computes a composite 'shutdown_vulnerability_score' for each region.
    """
    logging.info("Calculating shutdown vulnerability scores...")
    df['shutdown_vulnerability_score'] = (
        0.4 * df['federal_employment_density'] +
        0.3 * df['contractor_dependence'] +
        0.2 * df['unemployment_rate'] +
        0.1 * df['benefit_dependency_rate']
    )
    return df

def forecast_trends(df):
    """
    Forecasts risk trends for the next 3 months using linear regression.
    """
    logging.info("Forecasting risk trends...")
    # Assuming 'date' column exists for time series
    X = df[['date']]
    y = df['shutdown_vulnerability_score']
    model = ols('shutdown_vulnerability_score ~ date', data=df).fit()

    # Predict for the next 3 months (adjust dates as needed)
    future_dates = pd.date_range(start=df['date'].max() + pd.Timedelta(days=30), periods=3, freq='M')
    future_df = pd.DataFrame({'date': future_dates})
    predictions = model.predict(future_df)
    df = df.assign(predicted_risk=predictions)
    return df

def generate_summary(df):
    """
    Generates a summary of key statistics.
    """
    logging.info("Generating risk summary statistics...")
    summary = {
        'highest_risk_states': df.loc[df['shutdown_vulnerability_score'].idxmax(), ['state', 'shutdown_vulnerability_score']],
        'mean_risk': df['shutdown_vulnerability_score'].mean(),
        'variance_risk': df['shutdown_vulnerability_score'].var()
    }
    return summary

def main():
    # Load cleaned data
    data_path = './data/processed/merged_clean.csv'
    df = pd.read_csv(data_path)

    # Calculate vulnerability scores
    df = calculate_scores(df)

    # Forecast trends for the next 3 months
    df = forecast_trends(df)

    # Generate summary statistics
    summary = generate_summary(df)
    logging.info(f"Summary: {summary}")

    # Save updated data
    df.to_csv('./data/processed/regional_risk.csv', index=False)

    # Optional: Simple visual sanity checks (using matplotlib)
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 6))
    plt.plot(df['date'], df['shutdown_vulnerability_score'], label='Actual')
    plt.plot(df['date'], df['predicted_risk'], label='Predicted')
    plt.xlabel('Date')
    plt.ylabel('Shutdown Vulnerability Score')
    plt.title('Risk Trend Forecast')
    plt.legend()
    plt.savefig('./data/visuals/risk_trend_forecast.png')
    plt.close()

if __name__ == "__main__":
    main()

