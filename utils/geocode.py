"""Geocoding helpers for county/state coordinate lookup.

This module loads a local `data/uscounties.csv` to provide a
normalized county->(lat,lng) lookup. The implementation prefers
``pandas`` when available and falls back to the stdlib ``csv``
reader. State names are normalized to 2-letter codes via
``normalize_state_name`` so lookups are consistent.
"""
import os
import re
import logging
import math

logger = logging.getLogger(__name__)

# Caches populated on first use
_COUNTY_DF = None
_COUNTY_LOOKUP = None


def normalize_state_name(state_name):
    """
    Normalize state names to 2-letter codes.

    Args:
        state_name: State name (full name or 2-letter code)

    Returns:
        2-letter state code (e.g., 'CA', 'NY') or None
    """
    if state_name is None:
        return None

    # treat NaN-like floats as missing; avoid importing pandas at module import
    try:
        if isinstance(state_name, float) and math.isnan(state_name):
            return None
    except Exception:
        pass

    state_str = str(state_name).strip().upper()

    # Map from common full state name -> 2-letter code
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

    # If already a 2-letter code, return it unchanged
    if len(state_str) == 2:
        return state_str

    # Map full name to code
    return state_map.get(state_str, state_str)


def _normalize_county_name(name: str) -> str:
    """Normalize county text for matching.

    Removes common suffixes (county, parish, city, etc.), lowercases,
    removes punctuation and collapses whitespace.
    """
    if name is None:
        return ''
    s = str(name).lower().strip()
    # remove common suffixes
    s = re.sub(r"\b(county|parish|city|borough|municipality|planning region|census area|town|township)\b", '', s)
    # remove punctuation
    s = re.sub(r'[^a-z0-9\s]', '', s)
    # collapse whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def _load_county_lookup():
    """Load `data/uscounties.csv` and build a normalized lookup.

    Returns a dict keyed by (normalized_county, 2-letter-state) -> (lat, lng).
    Caches both the raw table (_COUNTY_DF) and the lookup dict.
    """
    global _COUNTY_DF, _COUNTY_LOOKUP
    if _COUNTY_LOOKUP is not None:
        return _COUNTY_LOOKUP

    # locate CSV relative to this file
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'uscounties.csv'))
    lookup = {}
    # Prefer pandas if available; otherwise use the standard csv reader
    df = None
    try:
        import pandas as pd
        try:
            df = pd.read_csv(csv_path, dtype=str)
            _COUNTY_DF = df
        except Exception as e:
            logger.warning("Could not read uscounties.csv at %s using pandas: %s", csv_path, e)
            df = None
            _COUNTY_DF = None
    except Exception:
        df = None
        _COUNTY_DF = None

    if df is None:
        # try builtin csv reader
        try:
            import csv as _csv
            rows = []
            with open(csv_path, newline='', encoding='utf-8') as fh:
                reader = _csv.DictReader(fh)
                for r in reader:
                    rows.append(r)
            df = rows
        except Exception as e:
            logger.warning('Could not read uscounties.csv at %s using csv module: %s', csv_path, e)
            _COUNTY_DF = None
            _COUNTY_LOOKUP = lookup
            return lookup

    # handle both pandas DataFrame (if pandas used) and list-of-dicts (csv.DictReader)
    if hasattr(df, 'columns'):
        # pandas DataFrame path
        for col in ['county', 'county_ascii', 'county_full', 'state_id', 'lat', 'lng']:
            if col not in df.columns:
                df[col] = None

        # Build normalized county name column
        df['_county_norms'] = df.apply(lambda r: list({
            _normalize_county_name(r.get('county')),
            _normalize_county_name(r.get('county_ascii')),
            _normalize_county_name(r.get('county_full'))
        } - {''}), axis=1)

    # populate lookup for each normalized variant (use normalized 2-letter codes)
        for _, row in df.iterrows():
            state_raw = row.get('state_id')
            state_code = normalize_state_name(state_raw)
            lat = row.get('lat')
            lng = row.get('lng')
            try:
                latf = float(lat) if lat not in (None, '') else None
                lngf = float(lng) if lng not in (None, '') else None
            except Exception:
                latf = None
                lngf = None

            if state_code is None:
                # skip rows missing a recognizable state
                continue

            norms = row.get('_county_norms') or []
            for n in norms:
                key = (n, state_code)
                # prefer first seen (dataset likely unique)
                if key not in lookup and latf is not None and lngf is not None:
                    lookup[key] = (latf, lngf)
    else:
        # list-of-dicts path (csv.DictReader) - normalize fields the same way
        for row in df:
            state_raw = row.get('state_id') or row.get('state') or row.get('state_name')
            state_code = normalize_state_name(state_raw)
            lat = row.get('lat') or row.get('latitude')
            lng = row.get('lng') or row.get('longitude')
            try:
                latf = float(lat) if lat not in (None, '') else None
                lngf = float(lng) if lng not in (None, '') else None
            except Exception:
                latf = None
                lngf = None

            if state_code is None:
                # skip rows missing a recognizable state
                continue

            norms = set()
            for col in ('county', 'county_ascii', 'county_full'):
                norms.add(_normalize_county_name(row.get(col)))
            norms.discard('')

            for n in norms:
                key = (n, state_code)
                if key not in lookup and latf is not None and lngf is not None:
                    lookup[key] = (latf, lngf)

    _COUNTY_LOOKUP = lookup
    return lookup


def get_county_coordinates(county_name, state_name):
    """Return (lat, lng) for a given county and state.

    Attempts a county-level lookup first. If that fails, falls back to a
    predefined state center. If the state is unrecognized, returns the
    continental US center.
    """
    # Predefined state center coordinates (fallback)
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
    if state_code is None:
        # fallback: center of US
        return (39.8283, -98.5795)

    # try county-level lookup
    try:
        lookup = _load_county_lookup()
        if county_name:
            cn = _normalize_county_name(county_name)
            key = (cn, state_code)
            if key in lookup:
                return lookup[key]

            # If exact normalized key not found, try searching for any key with same county normalized or fuzzy match
            # simple heuristic: check keys with same state and county substring
            for (k_county, k_state), coords in lookup.items():
                if k_state == state_code and (cn == k_county or cn in k_county or k_county in cn):
                    return coords
    except Exception as e:
        logger.debug('County lookup failed: %s', e)

    # fallback to state center
    if state_code in state_centers:
        return state_centers[state_code]

    return (39.8283, -98.5795)

