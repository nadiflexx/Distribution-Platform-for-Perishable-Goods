from unittest.mock import patch

from distribution_platform.app.config.constants import AppPhase
from distribution_platform.app.views.splash_view import SplashView


def test_render_splash():
    with (
        patch("distribution_platform.app.views.splash_view.LoaderOverlay") as loader,
        patch("distribution_platform.app.views.splash_view.SessionManager") as sm,
        patch("time.sleep") as sleep,
    ):
        view = SplashView()
        view.render()

        loader.static.assert_called_once()
        sleep.assert_called_once()
        sm.set_phase.assert_called_with(AppPhase.FORM)
