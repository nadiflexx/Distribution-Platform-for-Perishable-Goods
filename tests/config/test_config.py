from pathlib import Path
from unittest.mock import patch

from distribution_platform.config.enums import DataTypesEnum, WorkflowError
from distribution_platform.config.settings import ExternalServices, MapConfig, Paths


class TestSettings:
    def test_paths_structure(self):
        """Verifica que las rutas principales sean objetos Path."""
        assert isinstance(Paths.ROOT, Path)
        assert isinstance(Paths.DATA, Path)
        assert isinstance(Paths.LOGS, Path)

    @patch("pathlib.Path.mkdir")
    def test_make_dirs(self, mock_mkdir):
        """Verifica que make_dirs intenta crear los directorios críticos."""
        Paths.make_dirs()
        assert mock_mkdir.called
        assert mock_mkdir.call_count >= 5

    def test_app_config_structure(self):
        """Verifica claves esenciales en la configuración de la App."""
        assert ExternalServices.SCOPES == ["https://www.googleapis.com/auth/drive"]

    def test_map_config_colors(self):
        """Verifica que la lista de colores no esté vacía."""
        assert isinstance(MapConfig.ROUTE_COLORS, list)
        assert len(MapConfig.ROUTE_COLORS) > 0


class TestEnums:
    def test_workflow_error_enum(self):
        """Verifica que WorkflowError se comporte como string (StrEnum)."""
        assert WorkflowError.FILE_ERROR == "FILE_ERROR"
        assert isinstance(WorkflowError.DB_ERROR, str)

    def test_data_types_enum(self):
        """Verifica la existencia de tipos de datos."""
        assert DataTypesEnum.CSV is not None
        assert DataTypesEnum.SQL is not None
