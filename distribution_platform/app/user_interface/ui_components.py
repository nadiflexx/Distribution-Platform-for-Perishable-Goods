import os
import random

import pandas as pd
import streamlit as st

from distribution_platform.config.paths import TRUCK_IMAGES
from distribution_platform.config.settings import ROUTE_COLORS
from distribution_platform.core.inference_engine.engine import InferenceMotor
from distribution_platform.core.knowledge_base import rules
from distribution_platform.core.knowledge_base.rules import (
    obtain_format_validation_rules,
    parse_truck_data,
)
from distribution_platform.core.services.modelos import ConfigCamion
from distribution_platform.core.services.optimizador_sistema import OptimizadorSistema
from distribution_platform.infrastructure.etl.etl_pipeline import run_etl
from distribution_platform.infrastructure.maps.maps import SpainMapRoutes
from distribution_platform.infrastructure.repositories.truck_repository import (
    CAMIONES_GRANDES,
    CAMIONES_MEDIANOS,
    add_camion_personalizado,
    get_camiones_personalizados,
    save_custom_truck_image,
)

# ======================================================================
#   HELPER: STYLING WRAPPERS
# ======================================================================


def start_card(title, icon="🔹"):
    """Inicia un contenedor visual estilo tarjeta."""
    st.markdown(
        f"""
    <div class="modern-card">
        <div class="card-header">
            <span class="card-icon">{icon}</span>
            <h3 class="card-title">{title}</h3>
        </div>
    """,
        unsafe_allow_html=True,
    )


def end_card():
    """Cierra el contenedor de tarjeta."""
    st.markdown("</div>", unsafe_allow_html=True)


# ======================================================================
#   INITIAL STATE
# ======================================================================


def init_state():
    defaults = {
        "page": "form",
        "connection_type": None,
        "df": None,
        "selected_truck_data": None,
        "ia_result": None,
        "load_success": False,
        "truck_validated": False,
        "truck_creation_in_progress": False,
        "truck_created_successfully": False,
        "selected_truck": None,
        "orders_df": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ======================================================================
#   TITLE
# ======================================================================


def render_title():
    st.markdown(
        """
        <div class="main-header">
            <h1>🚚 AI Delivery Planner</h1>
            <p>Planificación inteligente de rutas para productos perecederos.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ======================================================================
#   DATA SOURCE SELECTOR
# ======================================================================


def render_connection_selector():
    start_card("Fuente de Datos", icon="📂")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.info("Selecciona el origen de tus datos para comenzar el análisis.")

    with col2:
        connection = st.radio(
            "¿Cómo deseas cargar los datos?",
            ["Database", "Files"],
            key="connection_type",
            horizontal=True,
            help="Elige 'Database' para conexión directa o 'Files' para subir CSV/XLSX/TXT.",
        )

    file_inputs = {}

    if connection == "Files":
        st.markdown("---")
        st.write("#### 📄 Subida de Archivos CSV")

        # Grid layout for file uploaders
        c1, c2 = st.columns(2)
        with c1:
            file_inputs["clientes"] = st.file_uploader("👤 Clientes (dboClientes)")
            file_inputs["lineas_pedido"] = st.file_uploader(
                "📝 Líneas Pedido (dboLineasPedido)"
            )
            file_inputs["pedidos"] = st.file_uploader("📦 Pedidos (dboPedidos)")
        with c2:
            file_inputs["productos"] = st.file_uploader("🍎 Productos (dboProductos)")
            file_inputs["provincias"] = st.file_uploader(
                "📍 Provincias (dboProvincias)"
            )
            file_inputs["destinos"] = st.file_uploader("🏁 Destinos (dboDestinos)")

    end_card()
    return connection, file_inputs


# ======================================================================
#   DATA LOADING
# ======================================================================


def load_data(connection_type, file_inputs):
    """Load data from database or CSV files."""

    if connection_type == "Database":
        with st.spinner("🔌 Conectando a la base de datos..."):
            try:
                orders = run_etl(use_database=True)
            except Exception as e:
                st.error(f"❌ Error conectando a BD:\n{e}")
                st.session_state.load_success = False
                return None
    else:
        missing = [k for k, f in file_inputs.items() if f is None]
        if missing:
            st.error("❌ Faltan archivos:\n- " + "\n- ".join(missing))
            return None

        try:
            with st.spinner("🔄 Procesando archivos ETL..."):
                orders = run_etl(uploaded_files=file_inputs)
        except Exception as e:
            st.error(f"❌ Error ejecutando ETL con archivos:\n{e}")
            st.session_state.load_success = False
            return None

    # Validate result
    if orders is None or (hasattr(orders, "empty") and orders.empty):
        st.error("❌ El proceso ETL no retornó datos válidos.")
        return None

    st.toast(f"✅ Datos cargados correctamente ({len(orders)} registros).", icon="🎉")
    st.session_state.df = orders
    st.session_state.load_success = True


# ======================================================================
#   TRUCK SELECTOR
# ======================================================================


def render_truck_selector():
    start_card("Configuración de Flota", icon="🚛")

    if not st.session_state.load_success:
        st.warning(
            "⚠️ Por favor, carga los datos en la sección anterior para continuar."
        )
        end_card()
        return

    st.success("📦 Datos listos. Selecciona el vehículo para la ruta.")
    st.markdown("---")

    show_trucks_selection()

    disabled = (
        st.session_state.truck_creation_in_progress
        and not st.session_state.truck_created_successfully
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Centered button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "✔️ Confirmar Vehículo",
            disabled=disabled,
            type="primary",
            width="stretch",
        ):
            truck = validate_and_confirm_truck()
            if truck is not None:
                st.session_state.selected_truck = truck

    end_card()


def validate_and_confirm_truck():
    truck_data = st.session_state.selected_truck_data

    if not truck_data:
        st.error("❌ No se ha seleccionado ningún camión.")
        return

    is_valid, result = parse_truck_data(truck_data)

    if not is_valid:
        st.error(f"❌ Error convirtiendo datos: {result.get('error')}")
        return

    with st.spinner("🔍 El motor de IA está validando el vehículo..."):
        motor = InferenceMotor(rules.obtain_rules())
        validation_result = motor.evaluate(result)

    if validation_result.is_valid:
        st.success("✅ El camión seleccionado es VÁLIDO")
        st.session_state.truck_validated = True
        return result
    else:
        st.error("❌ El camión NO cumple los requisitos")
        st.session_state.truck_validated = False

    return None


def show_trucks_selection():
    col_opt, col_disp = st.columns([1, 2])

    with col_opt:
        st.write("**Tipo de Vehículo**")
        truck_type = st.radio(
            "Selecciona categoría:",
            ["Camión Grande", "Camión Mediano", "Camión Personalizado"],
            key="truck_type",
            label_visibility="collapsed",
        )

    if truck_type != "Camión Personalizado":
        st.session_state.truck_creation_in_progress = False
        st.session_state.truck_created_successfully = False

    with col_disp:
        if truck_type == "Camión Grande":
            _show_standard_truck(CAMIONES_GRANDES, TRUCK_IMAGES["large"])
        elif truck_type == "Camión Mediano":
            _show_standard_truck(CAMIONES_MEDIANOS, TRUCK_IMAGES["medium"])
        else:
            _show_custom_truck_selection()


# ======================================================================
#   STANDARD TRUCK SELECTION
# ======================================================================


def _show_standard_truck(trucks_dict, folder_path):
    selected_truck = st.selectbox(
        "Elige un modelo:",
        list(trucks_dict.keys()),
    )

    if selected_truck:
        data = trucks_dict[selected_truck]
        img_path = os.path.join(folder_path, data["imagen"])

        _display_truck_details(selected_truck, data, img_path)

        st.session_state.selected_truck_data = {
            "nombre": selected_truck,
            "capacidad": data["capacidad"],
            "consumo": data["consumo"],
            "velocidad_constante": data["velocidad_constante"],
            "precio_conductor_hora": data["precio_conductor_hora"],
            "imagen": data["imagen"],
        }


# ======================================================================
#   CUSTOM TRUCKS
# ======================================================================


def _show_custom_truck_selection():
    camiones_personalizados = get_camiones_personalizados()

    if camiones_personalizados:
        option = st.radio(
            "Acción:",
            ["Usar existente", "Crear nuevo"],
            horizontal=True,
            key="custom_option",
        )

        if option == "Usar existente":
            _show_existing_custom_truck(camiones_personalizados)
        else:
            _show_custom_truck_form()
    else:
        st.info("No hay camiones personalizados. ¡Crea el primero!")
        _show_custom_truck_form()


def _show_existing_custom_truck(camiones):
    custom_truck = st.selectbox(
        "Mis camiones personalizados:",
        list(camiones.keys()),
    )

    if custom_truck:
        data = camiones[custom_truck]
        img_path = os.path.join(TRUCK_IMAGES["custom"], data["imagen"])
        _display_truck_details(custom_truck, data, img_path)
        st.session_state.selected_truck_data = data | {"nombre": custom_truck}


# ======================================================================
#   DISPLAY TRUCK DETAILS (Beautiful HTML Card)
# ======================================================================


def _display_truck_details(name, data, img_path):
    # Determine image source
    if os.path.exists(img_path):
        # We need to render the image via streamlit to get the correct path if local,
        # but for HTML embedding in 'truck-display', simple paths are tricky in Streamlit.
        # So we use a hybrid approach: Columns inside the parent container.
        pass

    st.markdown(f"#### 📋 Ficha Técnica: {name}")

    c1, c2 = st.columns([1, 1.5])

    with c1:
        if os.path.exists(img_path):
            st.image(img_path, width="stretch")
        else:
            st.warning("⚠️ Imagen no encontrada")

    with c2:
        st.markdown(
            f"""
        <div class="truck-details" style="background:white; padding:10px; border-radius:8px;">
            <div class="detail-row"><strong>📦 Capacidad:</strong> <span>{data["capacidad"]} kg</span></div>
            <div class="detail-row"><strong>⛽ Consumo:</strong> <span>{data["consumo"]} L/100km</span></div>
            <div class="detail-row"><strong>🚀 Velocidad:</strong> <span>{data["velocidad_constante"]} km/h</span></div>
            <div class="detail-row"><strong>👨‍✈️ Coste Conductor:</strong> <span>{data["precio_conductor_hora"]} €/h</span></div>
        </div>
        """,
            unsafe_allow_html=True,
        )


# ======================================================================
#   CUSTOM TRUCK FORM
# ======================================================================


def _show_custom_truck_form():
    st.markdown("##### 🛠️ Especificaciones del Nuevo Camión")

    with st.form("custom_truck_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("🏷️ Nombre del Modelo")
            capacity = st.text_input("📦 Capacidad (kg)")
            image_file = st.file_uploader(
                "🖼 Imagen (PNG/JPG)", type=["png", "jpg", "jpeg"]
            )

        with col2:
            consumption = st.text_input("⛽ Consumo (L/100km)")
            speed = st.text_input("🚀 Velocidad (km/h)")
            price_driver = st.text_input("👨‍✈️ Coste Hora (€)")

        submitted = st.form_submit_button(
            "Guardar Vehículo", type="primary", width="stretch"
        )

        if not submitted:
            return

        # Validation Logic
        truck_data = {
            "nombre": name,
            "capacidad": capacity,
            "consumo": consumption,
            "velocidad_constante": speed,
            "precio_conductor_hora": price_driver,
        }

        validations = [rule(truck_data) for rule in obtain_format_validation_rules()]
        all_valid = True
        for v in validations:
            if not v.startswith("✔"):
                st.error(v)
                all_valid = False

        if not all_valid:
            return

        is_valid, transformed = parse_truck_data(truck_data)
        if not is_valid:
            st.error(f"Error de conversión: {transformed.get('error')}")
            return

        # Save image
        image_name = save_custom_truck_image(image_file, name)

        # Save truck
        ok = add_camion_personalizado(
            nombre=name,
            capacidad=capacity,
            consumo=consumption,
            velocidad_constante=speed,
            precio_conductor_hora=price_driver,
            imagen=image_name,
        )

        if ok:
            st.success("🎉 ¡Camión creado exitosamente!")
            preview_data = truck_data | {"imagen": image_name}

            # Update Session
            st.session_state.selected_truck_data = preview_data
            st.session_state.truck_created_successfully = True

            # Force rerun to update list or show details
            st.rerun()
        else:
            st.error("❌ Error guardando el camión.")


# ======================================================================
#   AI SIMULATION - BRAINCORE OPTIMIZATION
# ======================================================================


def simulate_ia(df, truck_data):
    """
    Ejecuta optimización de rutas usando el sistema braincore.

    Parameters
    ----------
    df : pd.DataFrame o list[list[Order]]
        Datos de pedidos del ETL.
    truck_data : dict
        Datos del camión seleccionado con claves:
        - capacidad: capacidad en kg
        - consumo: consumo en L/100km
        - velocidad_constante: velocidad en km/h
        - precio_conductor_hora: coste conductor €/h

    Returns
    -------
    dict
        Resultados con rutas optimizadas.
    """
    try:
        # Configurar camión desde los datos seleccionados
        config_camion = ConfigCamion(
            velocidad_constante=float(truck_data.get("velocidad_constante", 90.0)),
            consumo_combustible=float(truck_data.get("consumo", 30.0)),
            capacidad_carga=float(truck_data.get("capacidad", 1000.0)),
            salario_conductor_hora=float(truck_data.get("precio_conductor_hora", 15.0)),
            precio_combustible_litro=1.50,
            peso_unitario_default=1.0,
        )

        # Crear optimizador
        optimizador = OptimizadorSistema(
            config_camion=config_camion,
            origen_base="Mataró"  # Origen fijo en Mataró
        )

        # Optimizar entregas
        resultados = optimizador.optimizar_entregas(
            pedidos=df,
            generaciones=100,
            poblacion_tam=40
        )

        # Convertir resultados a formato compatible con la UI
        routes = []
        assignments_data = []
        pedidos_imposibles_data = []
        total_distancia = 0
        total_coste = 0
        total_ingresos = 0
        total_beneficio = 0

        # Extraer pedidos no entregables si existen
        pedidos_no_entregables = resultados.get("pedidos_no_entregables", [])
        print(f"DEBUG: pedidos_no_entregables encontrados: {len(pedidos_no_entregables)}")
        
        if pedidos_no_entregables:
            print(f"DEBUG: Procesando {len(pedidos_no_entregables)} pedidos imposibles")
            for pedido in pedidos_no_entregables:
                pedidos_imposibles_data.append({
                    "Pedido ID": pedido.pedido_id,
                    "Destino": pedido.destino,
                    "Peso (kg)": pedido.cantidad_producto,
                    "Caducidad (días)": pedido.caducidad,
                    "Motivo": "❌ Isla sin conexión terrestre"
                })
            print(f"DEBUG: pedidos_imposibles_data tiene {len(pedidos_imposibles_data)} elementos")

        for key, resultado in resultados.items():
            # Saltar la clave especial de pedidos no entregables
            if key == "pedidos_no_entregables":
                continue

            if resultado is None:
                continue

            try:
                # Crear ruta para el mapa
                route = {
                    "path": resultado.ruta_coordenadas,
                    "color": random.choice(ROUTE_COLORS),
                    "pedidos": resultado.lista_pedidos_ordenada,  # Información de pedidos para popups
                    "camion_id": resultado.camion_id,
                    "tiempos_llegada": getattr(resultado, 'tiempos_llegada', []),  # Tiempos de llegada en horas
                }
                routes.append(route)

                # Acumular métricas
                total_distancia += resultado.distancia_total_km
                total_coste += resultado.coste_total_ruta
                total_ingresos += resultado.ingresos_totales
                total_beneficio += resultado.beneficio_neto
            except Exception as e:
                st.error(f"Error procesando resultado del camión {key}: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
                continue

            # Crear filas de asignaciones
            for pedido in resultado.lista_pedidos_ordenada:
                assignments_data.append({
                    "Camión": resultado.camion_id,
                    "Pedido ID": pedido.pedido_id,
                    "Destino": pedido.destino,
                    "Peso (kg)": pedido.cantidad_producto,
                    "Caducidad (días)": pedido.caducidad,
                })

        # Crear DataFrames
        assignments_df = pd.DataFrame(assignments_data) if assignments_data else pd.DataFrame()
        pedidos_imposibles_df = pd.DataFrame(pedidos_imposibles_data) if pedidos_imposibles_data else pd.DataFrame()
        
        print(f"DEBUG: DataFrame pedidos_imposibles creado con {len(pedidos_imposibles_df)} filas")
        print(f"DEBUG: pedidos_imposibles_df.empty = {pedidos_imposibles_df.empty}")

        return {
            "num_trucks": len([r for r in resultados.values() if r is not None and r != pedidos_no_entregables]),
            "routes": routes,
            "assignments": assignments_df,
            "pedidos_imposibles": pedidos_imposibles_df,
            "total_distancia": round(total_distancia, 2),
            "total_coste": round(total_coste, 2),
            "total_ingresos": round(total_ingresos, 2),
            "total_beneficio": round(total_beneficio, 2),
            "resultados_detallados": {k: v for k, v in resultados.items() if k != "pedidos_no_entregables"},
        }

    except Exception as e:
        st.error(f"❌ Error en optimización: {str(e)}")
        return {
            "num_trucks": 0,
            "routes": [],
            "assignments": pd.DataFrame(),
            "error": str(e)
        }


# ======================================================================
#   FORM PAGE
# ======================================================================


def render_form_page():
    render_title()

    # 1. Data Connection
    connection_type, file_inputs = render_connection_selector()

    col_load, _ = st.columns([1, 3])
    with col_load:
        if st.button("📥 Cargar Datos", type="secondary"):
            load_data(connection_type, file_inputs)

    # 2. Truck Selection
    render_truck_selector()

    # 3. Generate Action
    if st.session_state.truck_validated:
        st.markdown("---")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("🚀 GENERAR RUTA ÓPTIMA", type="primary", width="stretch"):
                with st.spinner("🤖 La IA está calculando la ruta óptima..."):
                    print("Truck selected:", st.session_state.selected_truck_data)
                    st.session_state.ia_result = simulate_ia(
                        st.session_state.df,
                        st.session_state.selected_truck_data,
                    )
                    st.session_state.page = "routes"
                    st.rerun()


# ======================================================================
#   ROUTES PAGE
# ======================================================================


def render_routes_page():
    st.markdown(
        '<div class="main-header"><h1>🗺️ Resultados de la Ruta</h1></div>',
        unsafe_allow_html=True,
    )

    ia = st.session_state.get("ia_result")

    if ia is None:
        st.warning("⚠️ No hay rutas generadas. Vuelve al formulario.")
        if st.button("🔙 Volver"):
            st.session_state.page = "form"
            st.rerun()
        return

    # Metrics Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🚛 Camiones Necesarios", ia.get("num_trucks", 0))
    with c2:
        st.metric("📏 Distancia Total", f"{ia.get('total_distancia', 0):.2f} km")
    with c3:
        st.metric("💰 Coste Total", f"{ia.get('total_coste', 0):.2f} €")
    with c4:
        beneficio = ia.get('total_beneficio', 0)
        st.metric(
            "💵 Beneficio Neto",
            f"{beneficio:.2f} €",
            delta=f"{beneficio:.2f} €" if beneficio > 0 else None,
            delta_color="normal" if beneficio > 0 else "off"
        )

    # Segunda fila con ingresos
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.metric("💶 Ingresos Totales", f"{ia.get('total_ingresos', 0):.2f} €")
    with c2:
        margen = (beneficio / ia.get('total_ingresos', 1)) * 100 if ia.get('total_ingresos', 0) > 0 else 0
        st.metric("📊 Margen de Beneficio", f"{margen:.1f}%")

    st.markdown("---")

    # ========== PEDIDOS IMPOSIBLES - MOSTRAR SIEMPRE SI EXISTEN ==========
    pedidos_imposibles = ia.get("pedidos_imposibles")
    
    print(f"DEBUG RENDER: pedidos_imposibles = {pedidos_imposibles}")
    print(f"DEBUG RENDER: type = {type(pedidos_imposibles)}")
    if pedidos_imposibles is not None:
        print(f"DEBUG RENDER: len = {len(pedidos_imposibles)}, empty = {pedidos_imposibles.empty}")
    
    if pedidos_imposibles is not None and not pedidos_imposibles.empty:
        st.error(f"🚫 **ADVERTENCIA CRÍTICA:** {len(pedidos_imposibles)} pedidos NO pueden entregarse por carretera")
        
        with st.expander("⛔ Ver Detalles de Pedidos Inaccesibles", expanded=True):
            st.warning(
                "**🏝️ Destinos insulares sin conexión terrestre detectados:**\n\n"
                "Estos pedidos requieren transporte **marítimo** ⛴️ o **aéreo** ✈️"
            )
            
            # Mostrar tabla con formato
            st.dataframe(
                pedidos_imposibles,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Pedido ID": st.column_config.NumberColumn("📦 Pedido ID", format="%d"),
                    "Destino": st.column_config.TextColumn("🏝️ Destino Insular"),
                    "Peso (kg)": st.column_config.NumberColumn("⚖️ Peso (kg)", format="%.1f"),
                    "Caducidad (días)": st.column_config.NumberColumn("⏰ Caducidad", format="%d días"),
                    "Motivo": st.column_config.TextColumn("❌ Motivo"),
                }
            )
            
            st.info(f"💡 **Total de peso no entregable:** {pedidos_imposibles['Peso (kg)'].sum():.1f} kg")

    st.markdown("---")

    # Resumen global de todos los camiones
    start_card("Resumen de Flota", icon="🚚")
    if "resultados_detallados" in ia:
        # Crear tabla resumen
        resumen_data = []
        for _, resultado in ia["resultados_detallados"].items():
            if resultado is None:
                continue

            peso_total = sum(
                p.cantidad_producto for p in resultado.lista_pedidos_ordenada
            )

            resumen_data.append({
                "Camión": f"🚛 {resultado.camion_id}",
                "Pedidos": len(resultado.lista_pedidos_ordenada),
                "Peso (kg)": f"{peso_total:.1f}",
                "Distancia (km)": f"{resultado.distancia_total_km:.1f}",
                "Tiempo (h)": f"{resultado.tiempo_total_viaje_horas:.1f}",
                "Coste (€)": f"{resultado.coste_total_ruta:.2f}",
                "Ingresos (€)": f"{resultado.ingresos_totales:.2f}",
                "Beneficio (€)": f"{resultado.beneficio_neto:.2f}",
                "Estado": "✅" if resultado.valida else "⚠️"
            })

        if resumen_data:
            st.dataframe(pd.DataFrame(resumen_data), use_container_width=True, hide_index=True)
    end_card()

    st.markdown("---")

    # Selector de camión individual
    if "resultados_detallados" in ia:
        start_card("Detalle por Camión", icon="🗺️")

        # Obtener lista de camiones válidos
        camiones_disponibles = [
            resultado.camion_id
            for resultado in ia["resultados_detallados"].values()
            if resultado is not None
        ]

        if camiones_disponibles:
            selected_truck = st.selectbox(
                "Selecciona un camión para ver su ruta detallada:",
                camiones_disponibles,
                format_func=lambda x: f"🚛 Camión {x}"
            )

            # Mostrar detalles del camión seleccionado
            resultado = None
            for res in ia["resultados_detallados"].values():
                if res and res.camion_id == selected_truck:
                    resultado = res
                    break

            if resultado:
                # Métricas del camión
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📦 Pedidos", len(resultado.lista_pedidos_ordenada))
                with col2:
                    st.metric("📏 Distancia", f"{resultado.distancia_total_km:.1f} km")
                with col3:
                    st.metric("💶 Ingresos", f"{resultado.ingresos_totales:.2f} €")
                with col4:
                    st.metric("💵 Beneficio", f"{resultado.beneficio_neto:.2f} €")

                # Métricas adicionales
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("💰 Coste Total", f"{resultado.coste_total_ruta:.2f} €")
                with col2:
                    margen = (resultado.beneficio_neto / resultado.ingresos_totales * 100) if resultado.ingresos_totales > 0 else 0
                    st.metric("📊 Margen", f"{margen:.1f}%")
                with col3:
                    peso_total = sum(p.cantidad_producto for p in resultado.lista_pedidos_ordenada)
                    st.metric("⚖️ Carga", f"{peso_total:.1f} kg")

                st.markdown("---")

                # Mapa individual de este camión
                st.subheader("🗺️ Ruta en el Mapa")
                # Encontrar la ruta correspondiente a este camión en ia["routes"]
                # Las rutas están en el mismo orden que resultados_detallados
                truck_routes = []
                for idx, (_, res) in enumerate(ia["resultados_detallados"].items()):
                    if res and res.camion_id == selected_truck:
                        if idx < len(ia.get("routes", [])):
                            truck_routes = [ia["routes"][idx]]
                        break

                if truck_routes:
                    SpainMapRoutes().render(truck_routes)
                else:
                    st.warning("No se pudo cargar el mapa para este camión")

                st.markdown("---")

                # Información detallada
                col_left, col_right = st.columns(2)

                with col_left:
                    st.write("**📊 Métricas de Ruta:**")
                    st.write(f"- Distancia total: {resultado.distancia_total_km} km")
                    st.write(f"- Tiempo total: {resultado.tiempo_total_viaje_horas:.2f} h")
                    st.write(f"- Tiempo conducción: {resultado.tiempo_conduccion_pura_horas:.2f} h")
                    st.write(f"- Consumo: {resultado.consumo_litros:.2f} L")

                with col_right:
                    st.write("**💰 Desglose de Costes:**")
                    st.write(f"- Combustible: {resultado.coste_combustible:.2f} €")
                    st.write(f"- Conductor: {resultado.coste_conductor:.2f} €")
                    st.write(f"- **Total: {resultado.coste_total_ruta:.2f} €**")

                st.markdown("---")

                # Ruta completa
                st.write("**🗺️ Ruta Completa:**")
                st.write(" → ".join(resultado.ciudades_ordenadas))

                # Estado de validación
                if not resultado.valida:
                    st.warning(f"⚠️ {resultado.mensaje}")
                else:
                    st.success(f"✅ {resultado.mensaje}")

                st.markdown("---")

                # Tabla de pedidos de este camión
                st.write("**📦 Pedidos Asignados:**")
                pedidos_data = []
                for pedido in resultado.lista_pedidos_ordenada:
                    pedidos_data.append({
                        "Pedido ID": pedido.pedido_id,
                        "Destino": pedido.destino,
                        "Peso (kg)": pedido.cantidad_producto,
                        "Caducidad (días)": pedido.caducidad,
                    })
                st.dataframe(pd.DataFrame(pedidos_data), use_container_width=True, hide_index=True)

        end_card()

    st.markdown("---")

    # Data Card - Asignaciones globales
    start_card("Tabla Global de Asignaciones", icon="📊")
    if not ia["assignments"].empty:
        st.dataframe(ia["assignments"], use_container_width=True)
    else:
        st.info("No hay asignaciones para mostrar")
    end_card()

    if st.button("🔄 Nueva Simulación"):
        st.session_state.page = "form"
        st.rerun()
