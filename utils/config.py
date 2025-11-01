
# config.py

import os

# Replace with your actual IBM Cloud API key and IAM endpoint
API_KEY = os.environ.get('IBM_API_KEY', 'your_default_api_key')
IAM_ENDPOINT = os.environ.get('IAM_ENDPOINT', 'https://iam.cloud.ibm.com/identity/token')
WATSONX_URL = os.environ.get('WATSONX_URL', 'https://us-south.ml.cloud.ibm.com/ml/v1/text/generation')
MODEL_ID = os.environ.get('MODEL_ID', 'granite-3-8b-instruct')

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

