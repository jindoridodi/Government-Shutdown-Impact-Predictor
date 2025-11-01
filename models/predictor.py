
# predictor.py

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import logging

# Configure logging
logging.basicConfig(filename='predictor.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

def preprocess_data():
    """
    Loads, cleans, and merges datasets by region.
    Calculates a composite 'risk_score' based on weighted factors.
    Returns a DataFrame with 'risk_score' for each region.
    """
    logging.info("Starting data preprocessing...")

    # Load datasets
    federal_employment = pd.read_csv('/data/raw/federal_employment.csv')
    contracts = pd.read_csv('/data/raw/government_contracts.csv')
    unemployment = pd.read_csv('/data/raw/unemployment.csv')
    benefits = pd.read_csv('/data/raw/benefits.csv')

    # Cleaning and merging (assuming 'region' column exists in all files)
    merged_data = pd.merge(federal_employment, contracts, on='region', how='left')
    merged_data = pd.merge(merged_data, unemployment, on='region', how='left')
    merged_data = pd.merge(merged_data, benefits, on='region', how='left')

    # Calculate risk_score
    merged_data['federal_employment_density'] = merged_data['federal_employment'] / merged_data['population']  # Assuming 'population' column exists
    merged_data['contractor_dependence'] = merged_data['contract_value'] / merged_data['gdp']  # Assuming 'contract_value' and 'gdp' columns exist
    merged_data['unemployment_rate'] = merged_data['unemployment_rate'] / 100  # Normalize to percentage
    merged_data['benefit_dependency'] = merged_data['benefit_recipients'] / merged_data['population']

    merged_data['risk_score'] = (
        0.4 * merged_data['federal_employment_density'] +
        0.3 * merged_data['contractor_dependence'] +
        0.2 * merged_data['unemployment_rate'] +
        0.1 * merged_data['benefit_dependency']
    )

    logging.info("Data preprocessing completed.")
    return merged_data

def train_model(data):
    """
    Trains a RandomForestRegressor on the preprocessed data.
    """
    logging.info("Starting model training...")

    X = data[['federal_employment_density', 'contractor_dependence', 'unemployment_rate', 'benefit_dependency']]
    y = data['risk_score']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    logging.info("Model training completed.")
    return model

def predict_future_risk(model, new_data):
    """
    Predicts risk_scores for new data using the trained model.
    """
    logging.info("Starting risk predictions...")
    predictions = model.predict(new_data)
    return predictions

def save_results(predictions, region_list):
    """
    Saves predictions to a CSV file.
    """
    logging.info("Saving predictions to file...")
    result_df = pd.DataFrame({'region': region_list, 'predicted_risk_score': predictions})
    result_df.to_csv('/data/processed/regional_risk.csv', index=False)
    logging.info("Predictions saved.")

if __name__ == "__main__":
    # Preprocess data
    data = preprocess_data()

    # Train the model
    model = train_model(data)

    # Load new data for prediction (example - replace with actual data loading)
    new_data = pd.read_csv('/data/raw/new_regional_data.csv')  # Assuming new data has the same features

    # Make predictions
    predictions = predict_future_risk(model, new_data)

    # Save results
    save_results(predictions, new_data['region'].tolist())

