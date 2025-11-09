"""
IBM watsonx.ai Time Series client functions.
"""

import requests
from typing import Optional
from ibm_watsonx_ai import APIClient
from utils.config import API_KEY, PROJECT_ID, ENDPOINT, env_loaded
from utils.logger import logger
from models.constants import IAM_TOKEN_URL


def log_credentials_status():
    """Log credential loading status."""
    if env_loaded:
        logger.info("Successfully loaded .env file")
    else:
        logger.info("No .env file found, checking environment variables")

    if PROJECT_ID and API_KEY:
        source = ".env file" if env_loaded else "environment variables"
        logger.info(f"Credentials loaded from {source}: PROJECT_ID={'*' * min(len(str(PROJECT_ID)), 8)}..., API_KEY={'*' * min(len(str(API_KEY)), 8)}...")
        print(f"✓ Credentials loaded from {source}")
    else:
        logger.warning("Credentials not found in .env file or environment variables")
        print("⚠ Warning: API_KEY or PROJECT_ID not found in .env file or environment variables")


def get_iam_token(api_key: str) -> str:
    """Generate IAM token for IBM Cloud authentication."""
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(IAM_TOKEN_URL, data=data, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]


def initialize_client() -> APIClient:
    """Initialize IBM watsonx.ai client with credentials."""
    logger.info("Initializing watsonx.ai client...")
    
    api_key_loaded = API_KEY is not None and API_KEY != ""
    project_id_loaded = PROJECT_ID is not None and PROJECT_ID != ""
    
    logger.info(f"API_KEY loaded: {api_key_loaded}, PROJECT_ID loaded: {project_id_loaded}")
    
    if not API_KEY or not PROJECT_ID:
        error_msg = f"API_KEY and PROJECT_ID must be set in .env file or environment variables. API_KEY loaded: {api_key_loaded}, PROJECT_ID loaded: {project_id_loaded}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    credentials = {
        'apikey': API_KEY,
        'url': ENDPOINT
    }
    
    client = APIClient(credentials=credentials, project_id=PROJECT_ID)
    logger.info("watsonx.ai client initialized successfully.")
    return client

# Initialize credential logging on module import
log_credentials_status()

