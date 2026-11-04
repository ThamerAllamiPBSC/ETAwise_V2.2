"""QuickShip demonstration network, Florida.

Coordinates are APPROXIMATE county reference points, not branch street addresses.
They are used for county-level predictions; the map may show city markers separately.
Replace with the same Census county representative-point dataset used in Colab
for strict training/inference consistency before production use.
"""
from math import asin, cos, radians, sin, sqrt

# County-level coordinates (latitude, longitude), approximate decimal degrees.
COUNTIES = {
    "Miami-Dade": (25.61, -80.50),
    "Broward": (26.15, -80.49),
    "Palm Beach": (26.65, -80.45),
    "Collier": (26.12, -81.40),
    "Lee": (26.58, -81.89),
    "Sarasota": (27.18, -82.36),
    "Polk": (27.95, -81.70),
    "Volusia": (29.06, -81.15),
    "Marion": (29.21, -82.06),
    "Alachua": (29.68, -82.36),
    "Orange": (28.51, -81.32),
    "Hillsborough": (27.93, -82.35),
}

BRANCHES = {
    "QS-01": {"city": "Homestead", "county": "Miami-Dade"},
    "QS-02": {"city": "Fort Lauderdale", "county": "Broward"},
    "QS-03": {"city": "West Palm Beach", "county": "Palm Beach"},
    "QS-04": {"city": "Naples", "county": "Collier"},
    "QS-05": {"city": "Fort Myers", "county": "Lee"},
    "QS-06": {"city": "Sarasota", "county": "Sarasota"},
    "QS-07": {"city": "Lakeland", "county": "Polk"},
    "QS-08": {"city": "Daytona Beach", "county": "Volusia"},
    "QS-09": {"city": "Ocala", "county": "Marion"},
    "QS-10": {"city": "Gainesville", "county": "Alachua"},
}

METROS = {
    "Miami": {"county": "Miami-Dade"},
    "Orlando": {"county": "Orange"},
    "Tampa": {"county": "Hillsborough"},
}


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in kilometers."""
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 6371.0088 * 2 * asin(min(1.0, sqrt(a)))


def get_route(branch_id: str, metro_name: str) -> dict:
    """Resolve two dropdown selections into county-level geographic inputs."""
    if branch_id not in BRANCHES:
        raise ValueError(f"Unknown branch {branch_id!r}; choose from {list(BRANCHES)}")
    if metro_name not in METROS:
        raise ValueError(f"Unknown metro {metro_name!r}; choose from {list(METROS)}")
    branch = BRANCHES[branch_id]
    origin_county = branch["county"]
    destination_county = METROS[metro_name]["county"]
    origin_lat, origin_lon = COUNTIES[origin_county]
    destination_lat, destination_lon = COUNTIES[destination_county]
    return {
        "branch_id": branch_id,
        "branch_city": branch["city"],
        "destination_metro": metro_name,
        "origin_county": origin_county,
        "destination_county": destination_county,
        "origin_lat": origin_lat,
        "origin_lon": origin_lon,
        "destination_lat": destination_lat,
        "destination_lon": destination_lon,
        "straight_km": haversine_km(origin_lat, origin_lon, destination_lat, destination_lon),
    }
