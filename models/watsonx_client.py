
# watsonx_client.py

import requests
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Replace with your actual IBM Cloud API key and IAM token
API_KEY = 'YOUR_IBM_API_KEY'
IAM_TOKEN = 'YOUR_IAM_TOKEN'
WATSONX_AI_BASE_URL = 'https://api.watsonx.ibm.com/v1/text-generation/models/Granite-3-8b-instruct/generate'

def get_access_token(api_key):
    """
    Obtains an access token using the IBM Cloud API key.
    """
    auth = (
        'Bearer',
        f'{API_KEY}:{IAM_TOKEN}'
    )
    response = requests.post(
        'https://iam.cloud.ibm.com/oidc/token',
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    response.raise_for_status()
    return response.json()['access_token']

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
    http = requests.Session()
    http.mount('https://', adapter)
    http.mount('http://', adapter)

    try:
        response = http.post(WATSONX_AI_BASE_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return response.json()['choices'][0]['text']  # Return the generated summary
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during watsonx.ai call: {e}")
        # Implement more sophisticated error handling or retry logic as needed
        return None

