import folium
import requests
from streamlit_folium import st_folium

from distribution_platform.config.settings import MAP_DEFAULTS


class SpainMapRoutes:
    """Map of Spain with real road routes using OSRM."""

    # Servidor muy estable → mejor que project-osrm.org
    OSRM_SERVER = "https://routing.openstreetmap.de/routed-car"

    def __init__(self):
        self.center = MAP_DEFAULTS["center"]
        self.zoom = MAP_DEFAULTS["zoom_start"]
        self.tiles = MAP_DEFAULTS["tiles"]

    def get_osrm_route(self, start, end):
        """
        Funtion to get the real road route between two points using OSRM API.
        start = [lat, lon]
        end   = [lat, lon]
        Returns list of [lat, lon] with the real road route.
        """
        url = (
            f"{self.OSRM_SERVER}/route/v1/driving/"
            f"{start[1]},{start[0]};{end[1]},{end[0]}"
            f"?overview=full&geometries=geojson"
        )

        response = requests.get(url)

        if response.status_code != 200:
            print("OSRM status error:", response.status_code)
            return None

        data = response.json()

        if "routes" not in data or len(data["routes"]) == 0:
            print("OSRM routing error:", data)
            return None

        try:
            coords = data["routes"][0]["geometry"]["coordinates"]
            return [[lat, lon] for lon, lat in coords]  # swap lon/lat → lat/lon
        except Exception as e:
            print("OSRM geometry parse error:", e)
            return None

    def render(self, routes):
        """
        Render the map with the given routes.
        routes = [
            {
                "path": [[lat1, lon1], [lat2, lon2], [lat3, lon3]...],
                "color": "red"
            }
        ].
        """
        m = folium.Map(
            location=self.center, zoom_start=self.zoom, tiles="OpenStreetMap"
        )

        for route in routes:
            path = route["path"]
            color = route.get("color", "blue")

            # Dibujar cada tramo consecutivo del path
            for i in range(len(path) - 1):
                start = path[i]
                end = path[i + 1]

                real_path = self.get_osrm_route(start, end)

                if real_path:
                    folium.PolyLine(
                        locations=real_path,
                        color=color,
                        weight=4,
                        opacity=0.9,
                    ).add_to(m)
                else:
                    # fallback: línea recta
                    folium.PolyLine(
                        locations=[start, end],
                        color="gray",
                        weight=3,
                        dash_array="5,5",
                    ).add_to(m)

                # Marcar punto inicial de cada tramo
                folium.CircleMarker(
                    location=start, radius=6, color="blue", fill=True
                ).add_to(m)

            # Marcar último punto
            folium.CircleMarker(
                location=path[-1], radius=6, color="green", fill=True
            ).add_to(m)

        return st_folium(m, width=850, height=600)
