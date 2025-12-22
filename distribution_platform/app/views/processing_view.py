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
        # Show static loader during computation
        LoaderOverlay.static(
            "ENGINE OPTIMIZATION", "Solving VRP Matrix & Computing Routes..."
        )

        # Execute optimization
        result = OptimizationService.run()

        if result:
            SessionManager.set("ia_result", result)

            # Pre-inject the persistent loader HTML BEFORE rerun
            # This ensures there's no gap between processing and results loader
            LoaderOverlay.persistent_map_loader()

            # Small delay to ensure loader is rendered
            time.sleep(0.1)

            SessionManager.set_phase(AppPhase.RESULTS)
        else:
            time.sleep(3)
            SessionManager.set_phase(AppPhase.FORM)
