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
        """
        m = folium.Map(
            location=self.center, zoom_start=self.zoom, tiles="OpenStreetMap"
        )

        for route in routes:
            path = route["path"]
            color = route.get("color", "blue")
            pedidos = route.get("pedidos", [])
            camion_id = route.get("camion_id", "?")
            tiempos_llegada = route.get("tiempos_llegada", [])

            # 1. DIBUJAR LÍNEAS (Tramos de carretera)
            # Dibujamos toda la ruta física primero (incluyendo la vuelta)
            for i in range(len(path) - 1):
                start = path[i]
                end = path[i + 1]

                # Obtener ruta real OSRM
                real_path = self.get_osrm_route(start, end)

                if real_path:
                    folium.PolyLine(
                        locations=real_path,
                        color=color,
                        weight=4,
                        opacity=0.8,
                    ).add_to(m)
                else:
                    # Fallback línea recta
                    folium.PolyLine(
                        locations=[start, end],
                        color="gray",
                        weight=3,
                        dash_array="5,5",
                    ).add_to(m)

            # 2. MARCADOR DE ORIGEN (HOME) 🏠
            # Siempre es el primer punto del path
            if len(path) > 0:
                folium.Marker(
                    location=path[0],
                    popup=folium.Popup(
                        f"<b>🏢 BASE (Mataró)</b><br>Salida y Retorno<br>Camión {camion_id}",
                        max_width=200,
                    ),
                    icon=folium.Icon(color="darkblue", icon="home", prefix="fa"),
                    zIndexOffset=1000,  # Para que quede por encima de las líneas
                ).add_to(m)

            # 3. MARCADORES DE PEDIDOS (ENTREGAS) 📦 -> ✅
            # Los pedidos corresponden a path[1], path[2]... path[n]
            # path[0] es origen, path[-1] es vuelta a origen (si hay vuelta)

            for i, pedido in enumerate(pedidos):
                # La coordenada del pedido i está en path[i+1]
                if i + 1 >= len(path):
                    break  # Seguridad por si el path no cuadra

                coord_pedido = path[i + 1]

                # Datos para el popup
                tiempo_llegada_h = tiempos_llegada[i] if i < len(tiempos_llegada) else 0
                dias_llegada = tiempo_llegada_h / 24.0
                dias_limite = getattr(
                    pedido, "dias_totales_caducidad", pedido.caducidad
                )
                margen_dias = dias_limite - dias_llegada

                # Determinar estado de tiempo
                if margen_dias < 0:
                    estado_emoji = "❌"
                    estado_texto = f"CADUCADO ({abs(margen_dias):.1f} días tarde)"
                    color_estado = "red"
                elif margen_dias < 1:
                    estado_emoji = "⚠️"
                    estado_texto = f"LÍMITE (margen {margen_dias:.1f} días)"
                    color_estado = "orange"
                else:
                    estado_emoji = "✅"
                    estado_texto = f"A TIEMPO (margen {margen_dias:.1f} días)"
                    color_estado = "green"

                # Lógica: ¿Es el último pedido o uno intermedio?
                es_ultimo = i == len(pedidos) - 1

                if es_ultimo:
                    # ÚLTIMA ENTREGA: Icono Verde con Check o Bandera
                    icon_color = "green"
                    icon_name = "flag-checkered"  # o "check"
                    titulo_html = f'<h4 style="margin:0; color:green;">🏁 Última Entrega: #{pedido.pedido_id}</h4>'
                else:
                    # ENTREGA INTERMEDIA: Icono Naranja Caja
                    icon_color = "orange"
                    icon_name = "box"
                    titulo_html = f'<h4 style="margin:0; color:#1f77b4;">📦 Pedido #{pedido.pedido_id}</h4>'

                popup_html = f"""
                <div style="font-family: Arial; min-width: 200px;">
                    {titulo_html}
                    <hr style="margin: 5px 0;">
                    <b>📍 Destino:</b> {pedido.destino}<br>
                    <b>⚖️ Peso:</b> {pedido.cantidad_producto:.1f} kg<br>
                    <b>⏰ Caducidad:</b> {pedido.caducidad} días<br>
                    <b>🕐 Llegada:</b> día {dias_llegada:.1f}<br>
                    <hr style="margin: 5px 0;">
                    <div style="background: {color_estado}; color: white; padding: 4px; border-radius: 4px; text-align: center; font-size: 0.9em;">
                        <b>{estado_emoji} {estado_texto}</b>
                    </div>
                </div>
                """

                folium.Marker(
                    location=coord_pedido,
                    popup=folium.Popup(popup_html, max_width=280),
                    icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa"),
                ).add_to(m)

        return st_folium(m, width=None, height=520)
