"""
Splash/Loading Screen View
"""

import time

from distribution_platform.app.components.loaders import LoaderOverlay
from distribution_platform.app.config.constants import AppPhase
from distribution_platform.app.state.session_manager import SessionManager


class SplashView:
    """Initial loading screen."""

    def render(self):
        LoaderOverlay.static("SMART CARGO", "Initializing components...")
        time.sleep(2.5)
        SessionManager.set_phase(AppPhase.FORM)
