"""
External Geocoding Service Adapter.
Wrapper around Geopy/Nominatim with retry logic.
"""

import time

from geopy.geocoders import Nominatim

from distribution_platform.config.logging_config import log as logger

_geolocator = Nominatim(user_agent="braincore_enterprise_v1")


def fetch_coordinates(city_name: str, max_attempts: int = 5) -> str:
    """
    Robust geocoding with exponential backoff.

    Args:
        city_name: Name of the city to locate.
        max_attempts: Number of retries before falling back.

    Returns:
        "lat,lon" string.
    """
    attempt = 0
    wait_time = 1

    while attempt < max_attempts:
        try:
            location = _geolocator.geocode(f"{city_name}, España", timeout=10)
            if location:
                return f"{location.latitude},{location.longitude}"
        except Exception as e:
            logger.warning(
                f"Geocoding attempt {attempt + 1} failed for {city_name}: {e}"
            )

        time.sleep(wait_time)
        wait_time = min(wait_time * 2, 16)  # Cap wait at 16s
        attempt += 1

    logger.error(f"Could not geocode '{city_name}'. Using default fallback.")
    return "40.4168,-3.7038"  # Madrid Center
