import concurrent.futures

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

from distribution_platform.config.settings import MapConfig

MAP_DEFAULTS = MapConfig.DEFAULTS
OSRM_SERVER = MapConfig.OSRM_SERVER


class SpainMapRoutes:
    """Map of Spain with real road routes using OSRM, optimized with threading and caching."""

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
        try:
            url = (
                f"{OSRM_SERVER}/route/v1/driving/"
                f"{start[1]},{start[0]};{end[1]},{end[0]}"
                f"?overview=full&geometries=geojson"
            )
            # Timeout añadido para evitar bloqueos si el servidor falla
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                return None

            data = response.json()

            if "routes" not in data or len(data["routes"]) == 0:
                return None

            coords = data["routes"][0]["geometry"]["coordinates"]
            return [[lat, lon] for lon, lat in coords]  # swap lon/lat → lat/lon

        except Exception as e:
            print(f"OSRM Error: {e}")
            return None

    def _fetch_route_segment(self, segment_info):
        """Helper for parallel execution."""
        start, end, color = segment_info
        real_path = self.get_osrm_route(start, end)
        return (real_path, start, end, color)

    def render(self, routes):
        """
        Render the map with the given routes efficiently.
        Uses caching to prevent re-rendering on zoom/pan.
        """

        # 1. GENERAR CLAVE ÚNICA PARA CACHÉ
        # Creamos un ID basado en los camiones y puntos para saber si el mapa ha cambiado
        if not routes:
            unique_id = "empty_map"
        else:
            # Usamos IDs de camión y longitud del path para crear una firma única
            signatures = [
                f"{r.get('camion_id', '?')}-{len(r.get('path', []))}" for r in routes
            ]
            unique_id = f"map_{hash(''.join(signatures))}"

        # 2. VERIFICAR SI YA EXISTE EN MEMORIA (Evita re-renderizado al hacer zoom)
        if unique_id in st.session_state:
            # Si ya existe, lo devolvemos directo (0 segundos de carga)
            return st_folium(
                st.session_state[unique_id],
                width=None,
                height=520,
                returned_objects=[],  # Optimización: no devolver datos innecesarios a Streamlit
            )

        # 3. SI NO EXISTE, PROCESAR CON PANTALLA DE CARGA
        with st.spinner("🔄 Procesando rutas y conectando con satélite..."):
            m = folium.Map(
                location=self.center, zoom_start=self.zoom, tiles="OpenStreetMap"
            )

            # --- FASE 1: PREPARAR DATOS PARA PARALELISMO ---
            segments_to_fetch = []

            for route in routes:
                path = route["path"]
                color = route.get("color", "blue")

                # Recopilar todos los tramos de carretera necesarios
                for i in range(len(path) - 1):
                    start = path[i]
                    end = path[i + 1]
                    segments_to_fetch.append((start, end, color))

            # --- FASE 2: DESCARGAR RUTAS EN PARALELO (ThreadPool) ---
            # Esto hace todas las peticiones HTTP a la vez en lugar de una por una
            fetched_segments = []
            if segments_to_fetch:
                # Usamos 10 hilos simultáneos (ajustable según servidor)
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    fetched_segments = list(
                        executor.map(self._fetch_route_segment, segments_to_fetch)
                    )

            # --- FASE 3: DIBUJAR LÍNEAS EN EL MAPA ---
            # Dibujar los resultados obtenidos
            for real_path, start, end, color in fetched_segments:
                if real_path:
                    folium.PolyLine(
                        locations=real_path,
                        color=color,
                        weight=4,
                        opacity=0.8,
                    ).add_to(m)
                else:
                    # Fallback línea recta si falla OSRM
                    folium.PolyLine(
                        locations=[start, end],
                        color="gray",
                        weight=3,
                        dash_array="5,5",
                    ).add_to(m)

            # --- FASE 4: AÑADIR MARCADORES (Rápido, no requiere HTTP) ---
            for route in routes:
                path = route["path"]
                pedidos = route.get("pedidos", [])
                camion_id = route.get("camion_id", "?")
                tiempos_llegada = route.get("tiempos_llegada", [])

                # Marcador BASE
                if len(path) > 0:
                    folium.Marker(
                        location=path[0],
                        popup=folium.Popup(
                            f"<b>🏢 BASE (Mataró)</b><br>Salida y Retorno<br>Camión {camion_id}",
                            max_width=200,
                        ),
                        icon=folium.Icon(color="darkblue", icon="home", prefix="fa"),
                        zIndexOffset=1000,
                    ).add_to(m)

                # Marcadores PEDIDOS
                for i, pedido in enumerate(pedidos):
                    if i + 1 >= len(path):
                        break

                    coord_pedido = path[i + 1]

                    # Cálculos de tiempo (lógica original intacta)
                    tiempo_llegada_h = (
                        tiempos_llegada[i] if i < len(tiempos_llegada) else 0
                    )
                    dias_llegada = tiempo_llegada_h / 24.0
                    dias_limite = getattr(
                        pedido, "dias_totales_caducidad", pedido.caducidad
                    )
                    margen_dias = dias_limite - dias_llegada

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

                    es_ultimo = i == len(pedidos) - 1

                    if es_ultimo:
                        icon_color = "green"
                        icon_name = "flag-checkered"
                        titulo_html = f'<h4 style="margin:0; color:green;">🏁 Última Entrega: #{pedido.pedido_id}</h4>'
                    else:
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

            # --- FASE 5: GUARDAR EN CACHÉ Y RENDERIZAR ---
            st.session_state[unique_id] = m

            return st_folium(
                m,
                width=None,
                height=520,
                returned_objects=[],  # Optimización final
            )
