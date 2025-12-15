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
                "color": "red",
                "pedidos": [Order1, Order2, ...],  # Optional: order info for popups
                "camion_id": 1  # Optional: truck ID
            }
        ].
        """
        m = folium.Map(
            location=self.center, zoom_start=self.zoom, tiles="OpenStreetMap"
        )

        for route in routes:
            path = route["path"]
            color = route.get("color", "blue")
            pedidos = route.get("pedidos", [])
            camion_id = route.get("camion_id", "?")
            tiempos_llegada = route.get("tiempos_llegada", [])  # Tiempos en horas

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

                # Marcar punto inicial (origen - Mataró)
                if i == 0:
                    folium.Marker(
                        location=start,
                        popup=folium.Popup(f"<b>🏢 Origen</b><br>Mataró<br>Camión {camion_id}", max_width=200),
                        icon=folium.Icon(color="blue", icon="home", prefix="fa"),
                    ).add_to(m)
                else:
                    # Marcadores de destino con información del pedido
                    # i-1 porque el primer punto es origen, los demás son pedidos
                    if i - 1 < len(pedidos):
                        pedido = pedidos[i - 1]
                        
                        # Obtener tiempo de llegada
                        tiempo_llegada_h = tiempos_llegada[i - 1] if i - 1 < len(tiempos_llegada) else 0
                        dias_llegada = tiempo_llegada_h / 24.0
                        
                        # Verificar si llega a tiempo
                        dias_limite = getattr(pedido, 'dias_totales_caducidad', pedido.caducidad)
                        margen_dias = dias_limite - dias_llegada
                        
                        # Determinar color y estado
                        if margen_dias < 0:
                            estado_emoji = "❌"
                            estado_texto = f"CADUCADO ({abs(margen_dias):.1f} días tarde)"
                            color_estado = "red"
                        elif margen_dias < 1:
                            estado_emoji = "⚠️"
                            estado_texto = f"JUSTO A TIEMPO (margen {margen_dias:.1f} días)"
                            color_estado = "orange"
                        else:
                            estado_emoji = "✅"
                            estado_texto = f"A TIEMPO (margen {margen_dias:.1f} días)"
                            color_estado = "green"
                        
                        popup_html = f"""
                        <div style="font-family: Arial; min-width: 200px;">
                            <h4 style="margin: 0 0 8px 0; color: #1f77b4;">📦 Pedido #{pedido.pedido_id}</h4>
                            <hr style="margin: 5px 0;">
                            <b>📍 Destino:</b> {pedido.destino}<br>
                            <b>⚖️ Peso:</b> {pedido.cantidad_producto:.1f} kg<br>
                            <b>⏰ Caducidad:</b> {pedido.caducidad} días<br>
                            <b>🕐 Tiempo llegada:</b> {dias_llegada:.1f} días<br>
                            <b>💶 Valor:</b> {pedido.precio_venta:.2f} €<br>
                            <b>🚛 Camión:</b> {camion_id}<br>
                            <hr style="margin: 5px 0;">
                            <div style="background: {color_estado}; color: white; padding: 5px; border-radius: 3px; text-align: center;">
                                <b>{estado_emoji} {estado_texto}</b>
                            </div>
                        </div>
                        """
                        folium.Marker(
                            location=start,
                            popup=folium.Popup(popup_html, max_width=280),
                            icon=folium.Icon(color="orange", icon="box", prefix="fa"),
                        ).add_to(m)
                    else:
                        # Fallback si no hay info del pedido
                        folium.CircleMarker(
                            location=start, radius=6, color="orange", fill=True
                        ).add_to(m)

            # Marcar último punto con información del último pedido
            if pedidos:
                ultimo_pedido = pedidos[-1]
                
                # Obtener tiempo de llegada del último pedido
                tiempo_llegada_h = tiempos_llegada[-1] if tiempos_llegada else 0
                dias_llegada = tiempo_llegada_h / 24.0
                
                # Verificar si llega a tiempo
                dias_limite = getattr(ultimo_pedido, 'dias_totales_caducidad', ultimo_pedido.caducidad)
                margen_dias = dias_limite - dias_llegada
                
                # Determinar estado
                if margen_dias < 0:
                    estado_emoji = "❌"
                    estado_texto = f"CADUCADO ({abs(margen_dias):.1f} días tarde)"
                    color_estado = "red"
                elif margen_dias < 1:
                    estado_emoji = "⚠️"
                    estado_texto = f"JUSTO A TIEMPO (margen {margen_dias:.1f} días)"
                    color_estado = "orange"
                else:
                    estado_emoji = "✅"
                    estado_texto = f"A TIEMPO (margen {margen_dias:.1f} días)"
                    color_estado = "green"
                
                popup_html = f"""
                <div style="font-family: Arial; min-width: 200px;">
                    <h4 style="margin: 0 0 8px 0; color: #2ca02c;">📦 Pedido #{ultimo_pedido.pedido_id}</h4>
                    <hr style="margin: 5px 0;">
                    <b>📍 Destino:</b> {ultimo_pedido.destino}<br>
                    <b>⚖️ Peso:</b> {ultimo_pedido.cantidad_producto:.1f} kg<br>
                    <b>⏰ Caducidad:</b> {ultimo_pedido.caducidad} días<br>
                    <b>🕐 Tiempo llegada:</b> {dias_llegada:.1f} días<br>
                    <b>💶 Valor:</b> {ultimo_pedido.precio_venta:.2f} €<br>
                    <b>🚛 Camión:</b> {camion_id}<br>
                    <span style="color: #2ca02c;">✅ Última entrega</span>
                    <hr style="margin: 5px 0;">
                    <div style="background: {color_estado}; color: white; padding: 5px; border-radius: 3px; text-align: center;">
                        <b>{estado_emoji} {estado_texto}</b>
                    </div>
                </div>
                """
                folium.Marker(
                    location=path[-1],
                    popup=folium.Popup(popup_html, max_width=250),
                    icon=folium.Icon(color="green", icon="check", prefix="fa"),
                ).add_to(m)
            else:
                folium.CircleMarker(
                    location=path[-1], radius=6, color="green", fill=True
                ).add_to(m)

        return st_folium(m, width=None, height=520)
