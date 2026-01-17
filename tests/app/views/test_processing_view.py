from unittest.mock import patch

import pytest

from distribution_platform.app.config.constants import AppPhase
from distribution_platform.app.views.processing_view import ProcessingView


@pytest.fixture
def mock_deps():
    with (
        patch(
            "distribution_platform.app.views.processing_view.LoaderOverlay"
        ) as loader,
        patch(
            "distribution_platform.app.views.processing_view.OptimizationService"
        ) as opt,
        patch("distribution_platform.app.views.processing_view.SessionManager") as sm,
        patch("time.sleep") as sleep,
    ):
        yield loader, opt, sm, sleep


def test_render_success(mock_deps):
    loader, opt, sm, _ = mock_deps

    result = {"data": "ok"}
    opt.run.return_value = result

    view = ProcessingView()
    view.render()

    loader.static.assert_called_once()
    opt.run.assert_called_once()
    sm.set.assert_called_with("ia_result", result)
    sm.set_phase.assert_called_with(AppPhase.RESULTS)
