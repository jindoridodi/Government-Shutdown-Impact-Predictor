
# watsonx_client.py

import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Replace with your actual IBM Cloud IAM token (optional). We'll load API_KEY from environment or .env.
# Keep IAM_TOKEN for backward compatibility if you want to supply it directly.
IAM_TOKEN = os.getenv('IAM_TOKEN', 'YOUR_IAM_TOKEN')

# Module-level API_KEY (loaded from .env or environment variable)
API_KEY = os.getenv('API_KEY', 'YOUR_IBM_API_KEY')
WATSONX_AI_BASE_URL = 'https://api.watsonx.ibm.com/v1/text-generation/models/Granite-3-8b-instruct/generate'

def get_access_token(api_key):
    """
    Obtains an access token using the IBM Cloud API key.
    """
    # IBM Cloud IAM token endpoint expects form-encoded data with the apikey and the grant_type
    url = 'https://iam.cloud.ibm.com/identity/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {
        'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
        'apikey': api_key
    }
    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()
    return response.json().get('access_token')

def summarize_impact(region_data):
    """
    Summarizes the key economic and social impacts by region using watsonx.ai.
    """
    headers = {
        'Authorization': f'Bearer {get_access_token(API_KEY)}',
        'Content-Type': 'application/json'
    }

    prompt = "Summarize the key economic and social impacts by region in plain English."
    data = {
        'prompt': prompt,
        'max_tokens': 150,  # Adjust as needed
        'temperature': 0.7,  # Control creativity/randomness
        'top_p': 0.95,  # Nucleus sampling parameter
        'frequency_penalty': 0.0,
        'presence_penalty': 0.0
    }

    retry_strategy = Retry(
        total=3,  # Number of retries
        backoff_factor=1,  # Factor to multiply wait time by after each retry
        status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    # Use a session context manager so the session/connection pool is properly closed
    try:
        with requests.Session() as http:
            http.mount('https://', adapter)
            http.mount('http://', adapter)
            response = http.post(WATSONX_AI_BASE_URL, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            # Be defensive about the returned JSON structure
            resp_json = response.json()
            choices = resp_json.get('choices') or []
            if choices and isinstance(choices, list):
                first = choices[0]
                # try multiple possible keys for text
                return first.get('text') or first.get('output_text') or None
            # Fallback to returning the whole response text if structure is unexpected
            return resp_json
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during watsonx.ai call: {e}")
        # Implement more sophisticated error handling or retry logic as needed
        return None

