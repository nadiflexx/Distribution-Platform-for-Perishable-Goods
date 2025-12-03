import folium
from streamlit_folium import st_folium
import streamlit as st
import requests


class SpainMapRoutes:
    """Map of Spain with real road routes using OSRM."""

    def __init__(self):
        self.center = [40.2, -3.5]
        self.zoom = 6

    def get_osrm_route(self, start, end):
        """
        start = [lat, lon]
        end = [lat, lon]
        """

        url = (
            f"https://router.project-osrm.org/route/v1/driving/"
            f"{start[1]},{start[0]};{end[1]},{end[0]}"
            f"?overview=full&geometries=geojson"
        )

        response = requests.get(url)

        if response.status_code != 200:
            return None

        data = response.json()

        try:
            coords = data["routes"][0]["geometry"]["coordinates"]
            # OSRM returns [lon, lat] → Folium uses [lat, lon]
            return [[lat, lon] for lon, lat in coords]
        except:
            return None

    def render(self, routes):
        """
        routes = [
            {
                "path": [[lat1, lon1], [lat2, lon2]],
                "color": "red"
            }
        ]
        """

        m = folium.Map(
            location=self.center, zoom_start=self.zoom, tiles="OpenStreetMap"
        )

        for route in routes:
            start = route["path"][0]
            end = route["path"][1]

            # Obtener ruta real por carretera
            real_path = self.get_osrm_route(start, end)

            if real_path:
                folium.PolyLine(
                    locations=real_path,
                    color=route.get("color", "blue"),
                    weight=4,
                    opacity=0.9,
                ).add_to(m)
            else:
                # straight route fallback
                folium.PolyLine(
                    locations=[start, end],
                    color="gray",
                    weight=3,
                    dash_array="5,5",
                ).add_to(m)

            # start marker
            folium.CircleMarker(
                location=start, radius=6, color="blue", fill=True
            ).add_to(m)

            # end marker
            folium.CircleMarker(
                location=end, radius=6, color="green", fill=True
            ).add_to(m)

        return st_folium(m, width=750, height=550)
