"""
Geocoding utilities for county and state coordinates.
"""

def normalize_state_name(state_name):
    """
    Normalize state names to 2-letter codes.
    
    Args:
        state_name: State name (full name or 2-letter code)
    
    Returns:
        2-letter state code (e.g., 'CA', 'NY')
    """
    if state_name is None:
        return None
    
    import pandas as pd
    if pd.isna(state_name):
        return None
    
    state_str = str(state_name).strip().upper()
    
    # State name to code mapping
    state_map = {
        'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR', 'CALIFORNIA': 'CA',
        'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE', 'FLORIDA': 'FL', 'GEORGIA': 'GA',
        'HAWAII': 'HI', 'IDAHO': 'ID', 'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA',
        'KANSAS': 'KS', 'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
        'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS', 'MISSOURI': 'MO',
        'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV', 'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ',
        'NEW MEXICO': 'NM', 'NEW YORK': 'NY', 'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH',
        'OKLAHOMA': 'OK', 'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
        'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT', 'VERMONT': 'VT',
        'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV', 'WISCONSIN': 'WI', 'WYOMING': 'WY',
        'DISTRICT OF COLUMBIA': 'DC', 'DC': 'DC'
    }
    
    # If already a 2-letter code, return it
    if len(state_str) == 2:
        return state_str
    
    # Map full name to code
    return state_map.get(state_str, state_str)


def get_county_coordinates(county_name, state_name):
    """
    Get approximate coordinates for a county using a simple lookup.
    
    For production, consider using a geocoding service or FIPS-based lookup.
    This is a simplified version that returns the approximate center of the state.
    You may want to use a proper geocoding library for more accurate county-level coordinates.
    
    Args:
        county_name: Name of the county (not currently used, but kept for API compatibility)
        state_name: Name or code of the state
    
    Returns:
        Tuple of (latitude, longitude) for the state center
    """
    # Simple fallback: return approximate center of state
    # In production, use a proper geocoding service or FIPS lookup table
    state_centers = {
        'AL': (32.806671, -86.791130), 'AK': (61.370716, -152.404419), 'AZ': (33.729759, -111.431221),
        'AR': (34.969704, -92.373123), 'CA': (36.116203, -119.681564), 'CO': (39.059811, -105.311104),
        'CT': (41.597782, -72.755371), 'DE': (39.318523, -75.507141), 'FL': (27.766279, -81.686783),
        'GA': (33.040619, -83.643074), 'HI': (21.094318, -157.498337), 'ID': (44.240459, -114.478828),
        'IL': (40.349457, -88.986137), 'IN': (39.849426, -86.258278), 'IA': (42.011539, -93.210526),
        'KS': (38.526600, -96.726486), 'KY': (37.668140, -84.670067), 'LA': (31.169546, -91.867805),
        'ME': (44.323535, -69.765261), 'MD': (39.063946, -76.802101), 'MA': (42.230171, -71.530106),
        'MI': (43.326618, -84.536095), 'MN': (45.694454, -93.900192), 'MS': (32.741646, -89.678696),
        'MO': (38.572954, -92.189283), 'MT': (46.921925, -110.454353), 'NE': (41.125370, -98.268082),
        'NV': (38.313515, -117.055374), 'NH': (43.452492, -71.563896), 'NJ': (40.298904, -74.521011),
        'NM': (34.840515, -106.248482), 'NY': (42.165726, -74.948051), 'NC': (35.630066, -79.806419),
        'ND': (47.528912, -99.784012), 'OH': (40.388783, -82.764915), 'OK': (35.565342, -96.928917),
        'OR': (44.572021, -122.070938), 'PA': (40.590752, -77.209755), 'RI': (41.680893, -71.51178),
        'SC': (33.856892, -80.945007), 'SD': (44.299782, -99.438828), 'TN': (35.747845, -86.692345),
        'TX': (31.054487, -97.563461), 'UT': (40.150032, -111.862434), 'VT': (44.045876, -72.710686),
        'VA': (37.769337, -78.169968), 'WA': (47.400902, -121.490494), 'WV': (38.491226, -80.954453),
        'WI': (44.268543, -89.616508), 'WY': (42.755966, -107.302490), 'DC': (38.907192, -77.036873)
    }
    
    state_code = normalize_state_name(state_name)
    if state_code in state_centers:
        return state_centers[state_code]
    # Default to center of US
    return (39.8283, -98.5795)

