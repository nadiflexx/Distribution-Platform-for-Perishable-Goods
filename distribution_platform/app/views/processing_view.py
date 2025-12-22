"""
Processing/Optimization Screen View
"""

import time

from distribution_platform.app.components.loaders import LoaderOverlay
from distribution_platform.app.config.constants import AppPhase
from distribution_platform.app.services.optimization_service import OptimizationService
from distribution_platform.app.state.session_manager import SessionManager


class ProcessingView:
    """Optimization processing screen."""

    def render(self):
        LoaderOverlay.static(
            "ENGINE OPTIMIZATION", "Solving VRP Matrix & Computing Routes..."
        )

        result = OptimizationService.run()

        if result:
            SessionManager.set("ia_result", result)
            SessionManager.set_phase(AppPhase.RESULTS)
        else:
            time.sleep(3)
            SessionManager.set_phase(AppPhase.FORM)
