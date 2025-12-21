"""
Base Routing Strategy.

Defines the interface for optimization algorithms and shares common
logic like driver schedule simulation (EU Regulations).
"""

from abc import ABC, abstractmethod

import pandas as pd

from distribution_platform.core.models.optimization import (
    RouteOptimizationResult,
    SimulationConfig,
)
from distribution_platform.core.models.order import Order

# Asumimos que GraphService estará en core/logic/graph.py (siguiente paso)
# Si aún no lo has movido, ajustaremos el import luego.


class RoutingStrategy(ABC):
    """Abstract Base Class for VRP Solvers."""

    def __init__(
        self,
        distance_matrix: pd.DataFrame,
        config: SimulationConfig,
        origin_city: str,
        graph_service=None,
    ):
        self.matrix = distance_matrix
        self.config = config
        self.origin = origin_city
        self.graph_service = graph_service

    @abstractmethod
    def optimize(self, orders: list[Order], **kwargs) -> RouteOptimizationResult | None:
        """Execute optimization strategy."""
        pass

    def _get_distance(self, origin: str, dest: str) -> float:
        """Safe matrix lookup."""
        if origin in self.matrix.index and dest in self.matrix.columns:
            return self.matrix.at[origin, dest]
        return 10000.0  # Penalización alta si no existe

    def _simulate_schedule(self, distance_km: float) -> tuple[float, float]:
        """
        Calculates real time and paid driving time based on Labor Rules.
        Fixed to prevent infinite loops on floating point precision issues.
        """
        if distance_km <= 0:
            return 0.0, 0.0

        speed = self.config.velocidad_constante
        if speed <= 0:
            speed = 90.0  # Fallback safety

        time_needed = distance_km / speed

        elapsed_time = 0.0
        paid_time = time_needed

        continuous_drive = 0.0
        daily_drive = 0.0

        rules = self.config.reglas_laborales

        # SAFETY: Limit iterations to avoid hanging (infinite loop protection)
        MAX_ITER = 10000
        iter_count = 0

        # Epsilon for float comparison
        EPS = 0.0001

        while time_needed > EPS and iter_count < MAX_ITER:
            iter_count += 1

            # Determinamos cuánto podemos conducir antes del próximo descanso
            time_to_short = rules.max_conduccion_seguida - continuous_drive
            time_to_daily = rules.max_conduccion_dia - daily_drive

            # El paso es lo más pequeño entre: lo que falta, límite corto, límite diario
            # Usamos max(EPS) para asegurar que siempre avanzamos algo
            step = min(time_needed, time_to_short, time_to_daily)

            # Si el paso es microscópico (error flotante), forzamos un avance mínimo o descanso
            if step < EPS:
                step = min(time_needed, 0.1)

            time_needed -= step
            elapsed_time += step
            continuous_drive += step
            daily_drive += step

            # Aplicar Descansos (con tolerancia EPS)
            if continuous_drive >= rules.max_conduccion_seguida - EPS:
                elapsed_time += rules.tiempo_descanso_corto
                continuous_drive = 0

            if daily_drive >= rules.max_conduccion_dia - EPS:
                elapsed_time += rules.tiempo_descanso_diario
                daily_drive = 0
                continuous_drive = 0  # El descanso largo resetea el acumulado corto

        if iter_count >= MAX_ITER:
            print(f"⚠️ Warning: Schedule simulation timeout for {distance_km}km")

        return elapsed_time, paid_time
