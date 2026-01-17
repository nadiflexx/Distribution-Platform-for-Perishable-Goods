from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest

from distribution_platform.config.enums import DataTypesEnum
from distribution_platform.infrastructure.persistence.file_reader import FileReader


class TestFileReader:
    # --- Load Data (Path) ---

    @patch("pathlib.Path.exists", return_value=False)
    def test_load_data_not_found(self, mock_exists):
        with pytest.raises(FileNotFoundError):
            FileReader.load_data(DataTypesEnum.CSV, "ghost.csv")

    @patch("pathlib.Path.exists", return_value=True)
    @patch(
        "distribution_platform.infrastructure.persistence.file_reader.FileReader._read_csv_smart"
    )
    def test_load_data_csv(self, mock_smart, mock_exists):
        FileReader.load_data(DataTypesEnum.CSV, "data.csv")
        mock_smart.assert_called_once()

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pandas.read_excel")
    def test_load_data_excel(self, mock_read_excel, mock_exists):
        FileReader.load_data(DataTypesEnum.EXCEL, "data.xlsx")
        mock_read_excel.assert_called_once()

    @patch("pathlib.Path.exists", return_value=True)
    def test_load_data_unsupported(self, mock_exists):
        with pytest.raises(ValueError):
            FileReader.load_data(DataTypesEnum.JSON, "data.json")

    # --- Load Uploaded File (Streamlit Buffer) ---

    def test_load_uploaded_csv_semicolon(self):
        """Prueba CSV con punto y coma."""
        data = "col1;col2\n1;2"
        mock_file = MagicMock()
        mock_file.name = "test.csv"
        mock_file.read.side_effect = BytesIO(data.encode()).read
        mock_file.__iter__.side_effect = BytesIO(data.encode()).__iter__

        with patch("pandas.read_csv") as mock_pd_read:
            FileReader.load_uploaded_file(mock_file)
            mock_pd_read.assert_called_with(mock_file, sep=";", engine="python")

    def test_load_uploaded_csv_comma_fallback(self):
        """Prueba fallback a coma si falla punto y coma."""
        mock_file = MagicMock()
        mock_file.name = "test.csv"

        with patch("pandas.read_csv", side_effect=[Exception("Error ;"), "Success"]):
            result = FileReader.load_uploaded_file(mock_file)
            mock_file.seek.assert_called_with(0)
            assert result == "Success"

    def test_load_uploaded_excel(self):
        mock_file = MagicMock()
        mock_file.name = "test.xlsx"

        with patch("pandas.read_excel") as mock_read:
            FileReader.load_uploaded_file(mock_file)
            mock_read.assert_called_once_with(mock_file)

    def test_load_uploaded_invalid_ext(self):
        mock_file = MagicMock()
        mock_file.name = "test.exe"

        with pytest.raises(ValueError):
            FileReader.load_uploaded_file(mock_file)

    # --- Utils ---

    def test_safe_concat(self):
        df1 = pd.DataFrame({"a": [1]})
        df2 = pd.DataFrame({"a": [2]})

        # Case: Empty list
        res_empty = FileReader.safe_concat([])
        assert res_empty.empty

        # Case: Valid list
        res = FileReader.safe_concat([df1, df2])
        assert len(res) == 2
        assert res.iloc[1]["a"] == 2

    @patch("pathlib.Path.mkdir")
    @patch("pandas.DataFrame.to_csv")
    def test_save_csv(self, mock_to_csv, mock_mkdir):
        df = pd.DataFrame({"a": [1]})
        path = Path("out/test.csv")

        FileReader.save_csv(df, path)

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_to_csv.assert_called_once_with(path, index=False)

    @patch("builtins.open", new_callable=mock_open, read_data="col1;col2")
    @patch("pandas.read_csv")
    def test_read_csv_smart_semicolon(self, mock_read, mock_file):
        FileReader._read_csv_smart(Path("test.csv"))
        mock_read.assert_called_with(Path("test.csv"), sep=";", engine="python")

    @patch("builtins.open", side_effect=Exception("Read Error"))
    @patch("pandas.read_csv")
    def test_read_csv_smart_exception(self, mock_read, mock_file):
        """Si falla al abrir para detectar, debe intentar leer con coma por defecto."""
        FileReader._read_csv_smart(Path("test.csv"))
        mock_read.assert_called_with(Path("test.csv"), sep=",", engine="python")
