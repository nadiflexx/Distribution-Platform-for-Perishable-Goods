from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from distribution_platform.batch.backup.backup import (
    authenticate_drive,
    create_drive_folder,
    upload_dataframe_to_drive,
)


@pytest.fixture
def sample_df():
    """Fixture que crea un DataFrame pequeño para pruebas."""
    return pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})


@pytest.fixture
def mock_drive_service():
    """Simula el objeto 'service' que devuelve la API de Google."""
    service = MagicMock()
    service.files.return_value.create.return_value.execute.return_value = {
        "id": "folder_123"
    }
    return service


class TestBackupGoogleDrive:
    @patch("distribution_platform.batch.backup.backup.Credentials")
    @patch("distribution_platform.batch.backup.backup.build")
    @patch("os.path.exists")
    def test_authenticate_drive_with_existing_token(
        self, mock_exists, mock_build, mock_creds
    ):
        """Prueba la autenticación cuando ya existe el token.json."""
        mock_exists.return_value = True
        mock_creds_instance = MagicMock()
        mock_creds_instance.valid = True
        mock_creds.from_authorized_user_file.return_value = mock_creds_instance

        authenticate_drive()

        mock_creds.from_authorized_user_file.assert_called_once()
        mock_build.assert_called_once_with(
            "drive", "v3", credentials=mock_creds_instance
        )

    def test_create_drive_folder(self, mock_drive_service):
        """Prueba la creación de carpetas llamando a la API simulada."""
        folder_id = create_drive_folder(mock_drive_service, "Backup_Test", "parent_123")

        assert folder_id == "folder_123"

        args, kwargs = mock_drive_service.files.return_value.create.call_args
        body = kwargs["body"]
        assert body["name"] == "Backup_Test"
        assert body["mimeType"] == "application/vnd.google-apps.folder"
        assert body["parents"] == ["parent_123"]

    @patch("distribution_platform.batch.backup.backup.MediaIoBaseUpload")
    def test_upload_dataframe_to_drive(
        self, mock_media_upload, mock_drive_service, sample_df
    ):
        """
        Prueba la subida de un DF.
        Verifica que se convierte a CSV en memoria y se llama a la API.
        """
        mock_drive_service.files.return_value.create.return_value.execute.return_value = {
            "id": "file_999"
        }

        upload_dataframe_to_drive(
            mock_drive_service, sample_df, "test.csv", "folder_123"
        )

        mock_media_upload.assert_called_once()

        args, kwargs = mock_drive_service.files.return_value.create.call_args
        assert kwargs["body"]["name"] == "test.csv"
        assert kwargs["body"]["parents"] == ["folder_123"]
        assert "media_body" in kwargs

    def test_create_drive_folder_error(self, mock_drive_service):
        """Prueba que la función lanza excepción si falla la API."""
        mock_drive_service.files.return_value.create.return_value.execute.side_effect = Exception(
            "API Down"
        )

        with pytest.raises(Exception, match="API Down"):
            create_drive_folder(mock_drive_service, "Error_Folder", "root")
