# config.py

import os
from dotenv import load_dotenv

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

# IBM watsonx.ai Configuration (loaded from .env file or environment variables)
# Use consistent naming: API_KEY (same as in predictor.py and watsonx_client.py)
API_KEY = os.getenv('API_KEY', os.getenv('IBM_API_KEY'))
PROJECT_ID = os.getenv('PROJECT_ID')
ENDPOINT = os.getenv('ENDPOINT', 'https://us-south.ml.cloud.ibm.com')

# Additional configuration
IAM_ENDPOINT = os.getenv('IAM_ENDPOINT', 'https://iam.cloud.ibm.com/identity/token')
WATSONX_URL = os.getenv('WATSONX_URL', os.getenv('ENDPOINT', 'https://us-south.ml.cloud.ibm.com/ml/v1/text/generation'))
MODEL_ID = os.getenv('MODEL_ID', 'granite-3-8b-instruct')

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
        'PROJECT_ID': PROJECT_ID,
        'ENDPOINT': ENDPOINT,
        'IAM_ENDPOINT': IAM_ENDPOINT,
        'WATSONX_URL': WATSONX_URL,
        'MODEL_ID': MODEL_ID,
        'DATA_PATHS': DATA_PATHS,
        'env_loaded': env_loaded
    }

if __name__ == "__main__":
    config = get_config()
    print(config)

