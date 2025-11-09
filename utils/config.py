
# config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Replace with your actual IBM Cloud API key and IAM endpoint
# Use consistent naming: API_KEY (same as in predictor.py and watsonx_client.py)
API_KEY = os.getenv('API_KEY', os.getenv('IBM_API_KEY', 'your_default_api_key'))
IAM_ENDPOINT = os.getenv('IAM_ENDPOINT', 'https://iam.cloud.ibm.com/identity/token')
WATSONX_URL = os.getenv('WATSONX_URL', os.getenv('ENDPOINT', 'https://us-south.ml.cloud.ibm.com/ml/v1/text/generation'))
MODEL_ID = os.getenv('MODEL_ID', 'granite-3-8b-instruct')
PROJECT_ID = os.getenv('PROJECT_ID')

DATA_PATHS = {
    "raw": os.path.join(os.getcwd(), 'data/datasets/'),
    "processed": os.path.join(os.getcwd(), 'data/processed/'),
    "visuals": os.path.join(os.getcwd(), 'data/visuals/')
}

def get_config():
    """
    Safely loads configuration values from environment variables or defaults.
    """
    return {
        'API_KEY': API_KEY,
        'IAM_ENDPOINT': IAM_ENDPOINT,
        'WATSONX_URL': WATSONX_URL,
        'MODEL_ID': MODEL_ID,
        'DATA_PATHS': DATA_PATHS
    }

if __name__ == "__main__":
    config = get_config()
    print(config)

