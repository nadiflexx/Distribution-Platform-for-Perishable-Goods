"""
Optimization Data Models.

Defines configuration entities for truck physics/costs and
structured results for route optimization algorithms.
"""

from pydantic import BaseModel, Field

from distribution_platform.core.models.order import Order


# --- Sub-model for cleaner structure ---
class LaborRules(BaseModel):
    """European Driver Regulations (approx. EU 561/2006)."""

    max_conduccion_seguida: float = Field(
        default=2.0, description="Max continuous driving hours"
    )
    tiempo_descanso_corto: float = Field(
        default=0.33, description="Short break duration (20m)"
    )
    max_conduccion_dia: float = Field(
        default=8.0, description="Max daily driving hours"
    )
    tiempo_descanso_diario: float = Field(
        default=12.0, description="Daily rest duration"
    )


# --- Main Configuration ---
class SimulationConfig(BaseModel):
    """
    Physical and Economic Configuration for the Truck Simulation.
    Replaces 'ConfigCamion'.
    """

    # Physics
    velocidad_constante: float = Field(default=90.0, description="Average speed km/h")
    consumo_combustible: float = Field(default=30.0, description="Liters per 100km")
    capacidad_carga: float = Field(
        default=1000.0, description="Max load in kg or units"
    )

    # Economics
    salario_conductor_hora: float = Field(
        default=15.0, description="Driver cost per hour"
    )
    precio_combustible_litro: float = Field(
        default=1.50, description="Fuel price per liter"
    )

    # Logic Defaults
    peso_unitario_default: float = 1.0

    # Rules (Nested for better organization)
    reglas_laborales: LaborRules = Field(default_factory=LaborRules)


# --- Result Object ---
class RouteOptimizationResult(BaseModel):
    """
    Standardized output for any routing algorithm (GA, ILS, etc.).
    Replaces 'ResultadoRuta'.
    """

    camion_id: int

    # Route Data
    lista_pedidos_ordenada: list[Order]
    ciudades_ordenadas: list[str]
    ruta_coordenadas: list[tuple[float, float]]
    tiempos_llegada: list[float] = Field(default_factory=list)

    # Physical Metrics
    distancia_total_km: float
    tiempo_total_viaje_horas: float
    tiempo_conduccion_pura_horas: float
    consumo_litros: float

    # Economic Metrics
    coste_combustible: float
    coste_conductor: float
    coste_total_ruta: float

    # Business Metrics
    ingresos_totales: float
    beneficio_neto: float

    # Validation Status
    valida: bool
    mensaje: str
