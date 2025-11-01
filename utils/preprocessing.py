
# preprocessing.py

import pandas as pd
import os

def load_data(file_paths):
    """
    Loads multiple CSV files into a list of DataFrames.
    """
    dataframes = []
    for file_path in file_paths:
        df = pd.read_csv(file_path)
        dataframes.append(df)
    return pd.concat(dataframes, ignore_index=True)

def clean_data(df):
    """
    Cleans the DataFrame by normalizing column names, filling missing values,
    and ensuring consistent data types.
    """
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    # Fill missing values (example: use median for numeric columns)
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

    # Ensure 'region' or 'FIPS' column exists for merging
    if 'region' not in df.columns and 'fips' not in df.columns:
        raise ValueError("Dataframe must contain 'region' or 'fips' column for merging.")

    return df

def feature_engineering(df):
    """
    Adds derived features to the DataFrame.
    """
    df['federal_employment_density'] = df['federal_employees'] / df['population']
    df['contractor_dependence'] = df['contract_value'] / df['GDP']
    return df

def save_clean_data(df, output_path):
    """
    Saves the cleaned DataFrame to a CSV file.
    """
    df.to_csv(output_path, index=False)

def main():
    # Define file paths
    file_paths = [
        os.path.join('/data/datasets', f) for f in os.listdir('/data/datasets') if f.endswith('.csv')
    ]

    # Load data
    logging.info("Loading data from CSV files...")
    raw_data = load_data(file_paths)

    # Clean data
    logging.info("Cleaning data...")
    cleaned_data = clean_data(raw_data)

    # Feature engineering
    logging.info("Adding derived features...")
    engineered_data = feature_engineering(cleaned_data)

    # Merge on 'region' or 'FIPS' (assuming one of these columns exists)
    merged_data = engineered_data.drop_duplicates(subset=['region'])  # Example: merge on 'region'

    # Remove duplicates
    merged_data = merged_data.drop_duplicates()

    # Ensure numeric columns are float
    numeric_cols = merged_data.select_dtypes(include=['number']).columns
    merged_data[numeric_cols] = merged_data[numeric_cols].astype(float)

    # Save cleaned data
    logging.info("Saving cleaned data to /data/processed/merged_clean.csv...")
    save_clean_data(merged_data, '/data/processed/merged_clean.csv')

if __name__ == "__main__":
    import logging
    logging.basicConfig(filename='preprocessing.log', level=logging.INFO, 
                        format='%(asctime)s:%(levelname)s:%(message)s')
    main()

