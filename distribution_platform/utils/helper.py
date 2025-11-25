from geopy.geocoders import Nominatim

import time


geolocator = Nominatim(user_agent="geoapi")


def get_coordinates(nombre):
    try:
        # Limpiar texto, quitar "Destino "
        consulta = nombre.replace("Destino ", "") + ", España"

        time.sleep(1)  # evitar bloqueo
        location = geolocator.geocode(consulta)

        if location:
            return f"{location.latitude},{location.longitude}"
    except:
        pass
    return None