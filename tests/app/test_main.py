from unittest.mock import patch

import pytest

from distribution_platform.app.main import Application, main


@pytest.fixture
def mock_app_deps():
    with (
        patch("distribution_platform.app.main.SessionManager") as sm,
        patch("distribution_platform.app.main.st") as st,
        patch("distribution_platform.app.main.Paths") as paths,
        patch("distribution_platform.app.main.SplashView") as splash,
        patch("distribution_platform.app.main.FormView") as form,
        patch("distribution_platform.app.main.ProcessingView") as proc,
        patch("distribution_platform.app.main.ResultsView") as res,
    ):
        yield sm, st, paths, splash, form, proc, res


def test_init_loads_config_and_css(mock_app_deps):
    sm, st, paths, _, _, _, _ = mock_app_deps

    # Scenario: CSS file exists
    paths.CSS_FILE.exists.return_value = True
    paths.CSS_FILE.read_text.return_value = "css content"

    Application()

    st.set_page_config.assert_called_once()
    # Called twice: once for shield, once for CSS
    assert st.markdown.call_count == 2
    sm.initialize.assert_called_once()


def test_init_no_css_file(mock_app_deps):
    _, st, paths, _, _, _, _ = mock_app_deps
    paths.CSS_FILE.exists.return_value = False

    Application()

    # Called once only for shield
    assert st.markdown.call_count == 1


def test_run_splash(mock_app_deps):
    _, st, _, splash, _, _, _ = mock_app_deps
    st.session_state = {"app_phase": "SPLASH"}

    app = Application()
    app.run()

    splash.return_value.render.assert_called_once()


def test_run_form(mock_app_deps):
    _, st, _, _, form, _, _ = mock_app_deps
    st.session_state = {"app_phase": "FORM"}

    app = Application()
    app.run()

    form.return_value.render.assert_called_once()


def test_run_unknown_state(mock_app_deps):
    _, st, _, _, _, _, _ = mock_app_deps
    st.session_state = {"app_phase": "UNKNOWN"}

    app = Application()
    app.run()

    st.error.assert_called_once()


def test_main_function():
    with patch("distribution_platform.app.main.Application") as mock_app_class:
        main()
        mock_app_class.return_value.run.assert_called_once()
