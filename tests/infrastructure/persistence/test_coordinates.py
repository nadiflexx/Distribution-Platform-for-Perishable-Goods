import json
from pathlib import Path
from unittest.mock import mock_open, patch

from distribution_platform.infrastructure.persistence.coordinates import CoordinateCache


class TestCoordinateCache:
    @patch("pathlib.Path.mkdir")
    def test_init_creates_directory(self, mock_mkdir):
        """Prueba que el constructor intenta crear el directorio."""
        path = Path("/fake/path/coords.json")
        CoordinateCache(path)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data='{"Madrid": "40,-3"}')
    def test_load_valid_json(self, mock_file, mock_exists):
        """Prueba la carga correcta de un JSON."""
        mock_exists.return_value = True

        cache = CoordinateCache(Path("dummy.json"))

        assert cache.get("Madrid") == "40,-3"
        assert len(cache.cache) == 1

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="INVALID JSON")
    def test_load_invalid_json(self, mock_file, mock_exists):
        """Prueba que maneja JSON corrupto sin romper."""
        mock_exists.return_value = True

        with patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)):
            cache = CoordinateCache(Path("dummy.json"))
            assert cache.cache == {}

    @patch("pathlib.Path.exists")
    def test_load_no_file(self, mock_exists):
        """Prueba cuando el archivo no existe."""
        mock_exists.return_value = False
        cache = CoordinateCache(Path("dummy.json"))
        assert cache.cache == {}

    @patch("builtins.open", new_callable=mock_open)
    def test_save_success(self, mock_file):
        """Prueba el guardado exitoso."""
        cache = CoordinateCache(Path("dummy.json"))
        cache.set("Toledo", "39,-4")

        cache.save()

        mock_file.assert_called_with(Path("dummy.json"), "w", encoding="utf-8")
        handle = mock_file()

        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        assert "Toledo" in written_content
        assert "39,-4" in written_content

    @patch("builtins.open", side_effect=PermissionError("No access"))
    def test_save_failure(self, mock_file):
        """Prueba manejo de errores al guardar (ej: permisos)."""
        cache = CoordinateCache(Path("dummy.json"))
        cache.save()

    def test_default_path_logic(self):
        """Prueba la lógica de fallback cuando no se pasa path."""
        with patch("pathlib.Path.resolve") as mock_resolve:
            mock_resolve.return_value.parents = [None, None, None, Path("/root")]

            with patch("pathlib.Path.mkdir"):
                cache = CoordinateCache()
                assert cache.cache_path == Path("/root/data/storage/coordinates.json")
