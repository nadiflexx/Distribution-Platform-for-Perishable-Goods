import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from distribution_platform.infrastructure.persistence.truck_repository import (
    TruckRepository,
)


@patch("distribution_platform.infrastructure.persistence.truck_repository.Paths")
class TestTruckRepository:
    def test_get_trucks_standard(self, mock_paths):
        """Prueba carga de camiones estándar (large/medium)."""
        repo = TruckRepository()

        fake_data = json.dumps(
            {"camiones_grandes": {"Volvo": {}}, "camiones_medianos": {"Mercedes": {}}}
        )

        with patch.object(
            repo, "_load_json", return_value=json.loads(fake_data)
        ) as mock_load:
            # Case 1: Large
            res = repo.get_trucks("large")
            assert "Volvo" in res

            # Case 2: Medium
            res = repo.get_trucks("medium")
            assert "Mercedes" in res

            # Verify filename
            mock_load.assert_called_with("large_medium_trucks.json")

    def test_get_trucks_custom(self, mock_paths):
        repo = TruckRepository()

        with patch.object(
            repo, "_load_json", return_value={"MiCamion": {}}
        ) as mock_load:
            res = repo.get_trucks("custom")
            assert "MiCamion" in res
            mock_load.assert_called_with("custom_trucks.json")

    def test_save_custom_truck(self, mock_paths):
        """Prueba flujo de guardar camión custom: leer existente -> actualizar -> guardar."""
        repo = TruckRepository()

        with (
            patch.object(repo, "_load_json", return_value={"Old": {}}),
            patch.object(repo, "_save_json", return_value=True) as mock_save,
        ):
            success = repo.save_custom_truck("Nuevo", {"capacidad": 1000})

            assert success is True
            mock_save.assert_called()
            saved_data = mock_save.call_args[0][1]
            assert "Old" in saved_data
            assert "Nuevo" in saved_data

    def test_save_image_success(self, mock_paths):
        """Prueba guardado de imagen con sanitización de nombre."""
        repo = TruckRepository()
        mock_paths.TRUCK_IMAGES = {"custom": Path("/fake/images")}

        # Mock Uploaded File
        mock_file = MagicMock()
        mock_file.name = "Foto.PNG"  # Mayúsculas
        mock_file.getbuffer.return_value = b"bytes"

        # Mock Write
        with (
            patch("pathlib.Path.write_bytes"),
            patch("pathlib.Path.mkdir"),
        ):
            filename = repo.save_image(mock_file, "Camión #1")

            assert filename.endswith(".png")
            assert "#" not in filename

    def test_save_image_no_file(self, mock_paths):
        repo = TruckRepository()
        assert repo.save_image(None, "name") == "truck_default.png"

    def test_save_image_error(self, mock_paths):
        """Si falla la escritura, devuelve default."""
        repo = TruckRepository()
        mock_file = MagicMock()
        mock_file.name = "test.jpg"

        with (
            patch("pathlib.Path.write_bytes", side_effect=Exception("Disk Full")),
            patch("pathlib.Path.mkdir"),
        ):
            res = repo.save_image(mock_file, "test")
            assert res == "test.jpg"

    # --- Internal Methods (_load_json / _save_json) ---

    def test_load_json_internal(self, mock_paths):
        repo = TruckRepository()
        mock_file_path = MagicMock()
        mock_paths.STORAGE.__truediv__.return_value = mock_file_path

        # Case: Exists
        mock_file_path.exists.return_value = True
        mock_file_path.read_text.return_value = '{"key": "value"}'

        data = repo._load_json("test.json")
        assert data == {"key": "value"}

        # Case: Not Exists
        mock_file_path.exists.return_value = False
        assert repo._load_json("test.json") == {}

        # Case: Bad JSON
        mock_file_path.exists.return_value = True
        mock_file_path.read_text.return_value = "INVALID"
        assert repo._load_json("test.json") == {}

    def test_save_json_internal(self, mock_paths):
        repo = TruckRepository()
        mock_file_path = MagicMock()
        mock_paths.STORAGE.__truediv__.return_value = mock_file_path

        # Case: Success
        assert repo._save_json("test.json", {}) is True
        mock_file_path.write_text.assert_called()

        # Case: Error
        mock_file_path.write_text.side_effect = Exception("Write Error")
        assert repo._save_json("test.json", {}) is False
