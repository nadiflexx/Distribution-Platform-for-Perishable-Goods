from datetime import datetime
import io
import os

from dotenv import load_dotenv

# --- Nuevas importaciones para OAuth ---
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# <--- 2. Cambiamos MediaFileUpload por MediaIoBaseUpload
from googleapiclient.http import MediaIoBaseUpload

# --- Importar tus módulos ---
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

# --- CONFIGURACIÓN ---
SCOPES = AppConfig.SCOPES
ROOT_DRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")
CREDENTIALS_FILE = os.getenv("GDRIVE_CREDENTIALS_PATH")
TOKEN_FILE = os.getenv("GDRIVE_TOKEN_PATH", "token.json")


def authenticate_drive():
    """Autentica usando credenciales de usuario (OAuth)."""
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
            print("⚠️ Primera ejecución: Se abrirá el navegador para autenticar...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def create_drive_folder(service, folder_name, parent_id):
    """Crea una carpeta en Google Drive y devuelve su ID."""
    try:
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        file = service.files().create(body=file_metadata, fields="id").execute()
        folder_id = file.get("id")
        print(f"📁 Carpeta creada en Drive: '{folder_name}' (ID: {folder_id})")
        return folder_id
    except Exception as e:
        print(f"❌ Error creando carpeta en Drive: {e}")
        raise e


def upload_dataframe_to_drive(service, df, file_name, folder_id):
    """
    Convierte un DataFrame a CSV en memoria y lo sube a Drive.
    No guarda nada en el disco local.
    """
    try:
        # 1. Convertir el DataFrame a un string CSV
        csv_content = df.to_csv(index=False, encoding="utf-8")

        # 2. Convertir ese string a bytes (stream en memoria)
        # Drive API prefiere trabajar con bytes
        fh = io.BytesIO(csv_content.encode("utf-8"))

        # 3. Preparar la subida desde memoria
        media = MediaIoBaseUpload(fh, mimetype="text/csv", resumable=True)
        file_metadata = {"name": file_name, "parents": [folder_id]}

        # 4. Subir
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        print(f"  ☁️ Subido desde memoria: file.id == {file.get('id')} / {file_name}")

    except Exception as e:
        print(f"  ❌ Error subiendo {file_name}: {e}")


def main():
    print("🚀 Iniciando proceso de exportación semanal (Solo Memoria)...")

    timestamp_folder = datetime.now().strftime("%Y-%m-%d_%H-%M")

    tasks = [
        {"func": load_clients, "name": "dboClientes.csv"},
        {"func": load_products, "name": "dboProductos.csv"},
        {"func": load_orders, "name": "dboPedidos.csv"},
        {"func": load_provinces, "name": "dboProvincias.csv"},
        {"func": load_destinations, "name": "dboDestinos.csv"},
        {"func": load_order_lines, "name": "dboLineasPedido.csv"},
    ]

    # 1. Autenticar
    try:
        drive_service = authenticate_drive()
    except Exception as e:
        print(f"❌ Error crítico de autenticación: {e}")
        return

    # 2. Carpeta Drive
    try:
        drive_folder_id = create_drive_folder(
            drive_service, "BACKUP_" + timestamp_folder, ROOT_DRIVE_FOLDER_ID
        )
    except Exception:
        return

    # 3. Procesar y Subir
    for task in tasks:
        try:
            print(f"⬇️ Recuperando datos: {task['name']}...")
            df = task["func"]()  # Llamada a SQL

            if df is not None and not df.empty:
                # Aquí llamamos a la nueva función pasando el DF directo
                upload_dataframe_to_drive(
                    drive_service, df, task["name"], drive_folder_id
                )
            else:
                print(f"⚠️ Dataset vacío para {task['name']}, saltando.")

        except Exception as e:
            print(f"❌ Error en tarea {task['name']}: {e}")

    print("🏁 Proceso finalizado correctamente.")


if __name__ == "__main__":
    main()
