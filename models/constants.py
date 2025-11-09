"""
Constants used across the prediction pipeline.
"""

# Model configuration
MIN_DATA_POINTS = 512  # Minimum required by GRANITE_TTM_512_96_R2 model
FORECAST_FREQUENCY = "M"  # Monthly frequency

# Risk index weights
RISK_WEIGHTS = {
    'employment_ratio': 0.4,
    'unemployment_rate': 0.3,
    'snap_rate': 0.2,
    'cost_index': 0.1
}

# Population estimation multiplier
POPULATION_ESTIMATE_MULTIPLIER = 50

# FIPS to state code mapping (first 2 digits of FIPS)
FIPS_TO_STATE = {
    '01': 'AL', '02': 'AK', '04': 'AZ', '05': 'AR', '06': 'CA', '08': 'CO', '09': 'CT',
    '10': 'DE', '11': 'DC', '12': 'FL', '13': 'GA', '15': 'HI', '16': 'ID', '17': 'IL',
    '18': 'IN', '19': 'IA', '20': 'KS', '21': 'KY', '22': 'LA', '23': 'ME', '24': 'MD',
    '25': 'MA', '26': 'MI', '27': 'MN', '28': 'MS', '29': 'MO', '30': 'MT', '31': 'NE',
    '32': 'NV', '33': 'NH', '34': 'NJ', '35': 'NM', '36': 'NY', '37': 'NC', '38': 'ND',
    '39': 'OH', '40': 'OK', '41': 'OR', '42': 'PA', '44': 'RI', '45': 'SC', '46': 'SD',
    '47': 'TN', '48': 'TX', '49': 'UT', '50': 'VT', '51': 'VA', '53': 'WA', '54': 'WV',
    '55': 'WI', '56': 'WY'
}

# IAM token endpoint
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"

# CSV encodings to try
CSV_ENCODINGS = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]

