import sys
from pathlib import Path

# Añade la raíz del proyecto al PYTHONPATH
ROOT = Path(__file__).resolve().parents[2]  
sys.path.append(str(ROOT))

from predictions.dashboard.layout import show_correlation_dashboard
from predictions.dashboard.config.config_dashboard import DashboardConfig


def run_correlations_dashboard(config: DashboardConfig | None = None):
    """
    Runs the correlation visualization dashboard.

    Parameters
    ----------
    config : DashboardConfig
        Dashboard configuration (title, default data path, layout…).
    """
    config = config or DashboardConfig()
    show_correlation_dashboard(config)


if __name__ == "__main__":
    run_correlations_dashboard()
