import time

from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="geoapi")


def get_coordinates(name):
    """Return coordinates for a Spanish place name as a 'lat,lon' string.

    Parameters
    ----------
    name : str
        Place name to geocode (in Spanish context).

    Returns
    -------
    str or None
        A string formatted as "latitude,longitude" when a location is found,
        otherwise None.

    Notes
    -----
    The function sleeps for 1 second to avoid rate limiting by the geocoding service.
    """
    try:
        request = name + ", España"

        time.sleep(1)  # evitar bloqueo
        location = geolocator.geocode(request)

        if location:
            return f"{location.latitude},{location.longitude}"
    except Exception:
        pass
    return None
