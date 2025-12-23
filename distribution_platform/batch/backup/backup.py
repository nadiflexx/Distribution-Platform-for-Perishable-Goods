from datetime import datetime
import io
import os

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from distribution_platform.config.logging_config import log as logger
from distribution_platform.config.settings import AppConfig
from distribution_platform.infrastructure.database.sql_client import (
    load_clients,
    load_destinations,
    load_order_lines,
    load_orders,
    load_products,
    load_provinces,
)

load_dotenv()

SCOPES = AppConfig.SCOPES
ROOT_DRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")
CREDENTIALS_FILE = os.getenv("GDRIVE_CREDENTIALS_PATH")
TOKEN_FILE = os.getenv("GDRIVE_TOKEN_PATH", "token.json")


def authenticate_drive():
    """Authenticates using user credentials (OAuth)."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            logger.warning("⚠️ First run: Browser will open for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def create_drive_folder(service, folder_name, parent_id):
    """Creates a folder in Google Drive and returns its ID."""
    try:
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        file = service.files().create(body=file_metadata, fields="id").execute()
        folder_id = file.get("id")
        logger.info(f"📁 Folder created in Drive: '{folder_name}' (ID: {folder_id})")
        return folder_id
    except Exception as e:
        logger.error(f"❌ Error creating folder in Drive: {e}")
        raise e


def upload_dataframe_to_drive(service, df, file_name, folder_id):
    """
    Converts a DataFrame to CSV in memory and uploads it to Drive.
    Does not save anything to local disk.
    """
    try:
        csv_content = df.to_csv(index=False, encoding="utf-8")

        fh = io.BytesIO(csv_content.encode("utf-8"))

        media = MediaIoBaseUpload(fh, mimetype="text/csv", resumable=True)
        file_metadata = {"name": file_name, "parents": [folder_id]}

        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        logger.info(
            f"  ☁️ Uploaded from memory: file.id == {file.get('id')} / {file_name}"
        )

    except Exception as e:
        logger.error(f"  ❌ Error uploading {file_name}: {e}")


def main():
    logger.info("🚀 Starting weekly export process (Memory Only)...")

    timestamp_folder = datetime.now().strftime("%Y-%m-%d_%H-%M")

    tasks = [
        {"func": load_clients, "name": "dboClientes.csv"},
        {"func": load_products, "name": "dboProductos.csv"},
        {"func": load_orders, "name": "dboPedidos.csv"},
        {"func": load_provinces, "name": "dboProvincias.csv"},
        {"func": load_destinations, "name": "dboDestinos.csv"},
        {"func": load_order_lines, "name": "dboLineasPedido.csv"},
    ]

    try:
        drive_service = authenticate_drive()
    except Exception as e:
        logger.critical(f"❌ Critical authentication error: {e}")
        return

    try:
        drive_folder_id = create_drive_folder(
            drive_service, "BACKUP_" + timestamp_folder, ROOT_DRIVE_FOLDER_ID
        )
    except Exception:
        return

    for task in tasks:
        try:
            logger.info(f"⬇️ Retrieving data: {task['name']}...")
            df = task["func"]()  # SQL Call

            if df is not None and not df.empty:
                upload_dataframe_to_drive(
                    drive_service, df, task["name"], drive_folder_id
                )
            else:
                logger.warning(f"⚠️ Empty dataset for {task['name']}, skipping.")

        except Exception as e:
            logger.error(f"❌ Error in task {task['name']}: {e}")

    logger.info("🏁 Process finished successfully.")


if __name__ == "__main__":
    main()
