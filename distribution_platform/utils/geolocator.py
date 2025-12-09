import time

from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="geoapi")


def get_coordinates(name, max_attempts=10):
    """Geocodificación robusta:
     Reintenta hasta 10 veces
    - Espera incremental (1s → 2s → 4s...)
    - Si falla → fallback seguro.
    """
    attempt = 0
    wait = 1  # segundos

    while attempt < max_attempts:
        try:
            location = geolocator.geocode(name + ", España")

            if location:
                return f"{location.latitude},{location.longitude}"

        except Exception:
            pass

        time.sleep(wait)
        wait = min(wait * 2, 30)
        attempt += 1

    # Fallback si NUNCA encuentra coordenadas
    print(f"[WARNING] Fallo geocoder → fallback para destino: {name}")
    return "40.4168,-3.7038"  # centro de España
