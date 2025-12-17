"""
Modelos de datos para el sistema de optimización de rutas braincore.

Este módulo define las configuraciones de camión y resultados de rutas.
El modelo de Pedido se reutiliza de distribution_platform.models.order.Order
"""

from pydantic import BaseModel, Field

from distribution_platform.core.models.order import Order


# --- Configuración del Camión y Reglas Laborales ---
class ConfigCamion(BaseModel):
    """Configuración de costes y reglas del conductor."""

    # Física del camión
    velocidad_constante: float = 90.0  # km/h
    consumo_combustible: float = 30.0  # L/100km
    capacidad_carga: float = 1000.0  # Capacidad máxima en kg

    # Costes
    salario_conductor_hora: float = 15.0  # €/hora (solo conducción)
    precio_combustible_litro: float = 1.50  # €/litro (estimado)

    # Reglas Laborales (Tiempos en horas)
    max_conduccion_seguida: float = 2.0  # Conducir 2h
    tiempo_descanso_corto: float = 0.33  # Descansar 20 min (0.33h)
    max_conduccion_dia: float = 8.0  # Max 8h al día
    tiempo_descanso_diario: float = 12.0  # Descanso largo tras 8h

    peso_unitario_default: float = 1.0


# --- Resultado de Optimización ---
class ResultadoRuta(BaseModel):
    """Resultado detallado listo para el Front."""

    camion_id: int

    # Datos de la ruta
    lista_pedidos_ordenada: list[Order]
    ciudades_ordenadas: list[str]
    # NUEVO: Coordenadas ordenadas para pintar la línea en el mapa sin buscar en JSON
    ruta_coordenadas: list[tuple[float, float]]
    # Tiempos de llegada a cada pedido (en horas desde el origen)
    tiempos_llegada: list[float] = Field(default_factory=list)

    # Estadísticas Físicas
    distancia_total_km: float
    tiempo_total_viaje_horas: float  # Incluye descansos (tiempo real que tarda)
    tiempo_conduccion_pura_horas: float  # Solo volante (para pagar al chofer)

    # Costes Económicos (Lo calculamos en backend)
    consumo_litros: float
    coste_combustible: float  # Euros
    coste_conductor: float  # Euros
    coste_total_ruta: float  # Euros (Gasolina + Chofer)

    # Ingresos y Beneficios
    ingresos_totales: float  # Euros - Suma de precio_venta de todos los pedidos
    beneficio_neto: float  # Euros - Ingresos - Costes

    valida: bool
    mensaje: str
