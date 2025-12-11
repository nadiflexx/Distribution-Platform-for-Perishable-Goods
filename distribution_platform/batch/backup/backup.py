from datetime import datetime
import os

from dotenv import load_dotenv

# --- Nuevas importaciones para OAuth ---
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- Importar tus módulos ---
from distribution_platform.config import paths
from distribution_platform.infrastructure.database.repository import (
    load_clients,
    load_destinations,
    load_order_lines,
    load_orders,
    load_products,
    load_provinces,
)

load_dotenv()

# --- CONFIGURACIÓN ---
SCOPES = paths.SCOPES
# El ID de la carpeta donde quieres guardar todo (El que está en tu .env)
ROOT_DRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")

# Rutas a los archivos de credenciales
CREDENTIALS_FILE = os.getenv("GDRIVE_CREDENTIALS_PATH")
TOKEN_FILE = os.getenv(
    "GDRIVE_TOKEN_PATH", "token.json"
)  # El archivo que se generará automáticamente


def authenticate_drive():
    """Autentica usando credenciales de usuario (OAuth) para usar TU espacio."""
    creds = None

    # 1. Intentar cargar token existente (para ejecución batch)
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # 2. Si no hay token o expiró, loguear al usuario
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # Si el refresh falla, forzamos nuevo login
                creds = None

        if not creds:
            print("⚠️ Primera ejecución: Se abrirá el navegador para autenticar...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # 3. Guardar el token para la próxima vez (Batch)
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


def upload_file_to_drive(service, file_path, file_name, folder_id):
    """Sube un archivo a una carpeta ESPECÍFICA en Drive."""
    try:
        file_metadata = {"name": file_name, "parents": [folder_id]}
        media = MediaFileUpload(file_path, mimetype="text/csv", resumable=True)

        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        print(f"  ☁️ Subido: {file_name}")

    except Exception as e:
        print(f"  ❌ Error subiendo {file_name}: {e}")


def main():
    print("🚀 Iniciando proceso de exportación semanal (Modo Usuario)...")

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
        print("Asegúrate de tener 'credentials.json' en la carpeta.")
        return

    # 2. Carpeta Drive
    try:
        drive_folder_id = create_drive_folder(
            drive_service, "BACKUP_" + timestamp_folder, ROOT_DRIVE_FOLDER_ID
        )
    except Exception:
        return

    # 4. Procesar
    for task in tasks:
        try:
            print(f"⬇️ Procesando: {task['name']}...")
            df = task["func"]()

            if df is not None and not df.empty:
                file_path = task["name"]
                df.to_csv(file_path, index=False, encoding="utf-8")
                upload_file_to_drive(
                    drive_service, str(file_path), task["name"], drive_folder_id
                )
            else:
                print(f"⚠️ Dataset vacío para {task['name']}, saltando.")

        except Exception as e:
            print(f"❌ Error en tarea {task['name']}: {e}")

    print("🏁 Proceso finalizado correctamente.")


if __name__ == "__main__":
    main()
