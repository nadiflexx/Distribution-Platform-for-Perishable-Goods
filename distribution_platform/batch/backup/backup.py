from datetime import datetime
import os

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- Importar tus módulos existentes ---
from distribution_platform.config import paths
from distribution_platform.infrastructure.database.repository import (
    load_clients,
    load_destinations,
    load_order_lines,
    load_orders,
    load_products,
    load_provinces,
)

# Cargar variables de entorno
load_dotenv()

# Configuración de Google Drive
SERVICE_ACCOUNT_FILE = os.getenv("GDRIVE_CREDENTIALS_PATH")
ROOT_DRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")
SCOPES = paths.SCOPES


def authenticate_drive():
    """Autentica con Google Drive usando Service Account."""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("drive", "v3", credentials=creds)
    return service


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
    """Sube un archivo a una carpeta ESPECÍFICA (folder_id) en Drive."""
    try:
        file_metadata = {"name": file_name, "parents": [folder_id]}
        media = MediaFileUpload(file_path, mimetype="text/csv", resumable=True)

        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        print(f"  ☁️ Subido: {file.get('id')} - {file_name}")

    except Exception as e:
        print(f"  ❌ Error subiendo {file_name}: {e}")


def main():
    print("🚀 Iniciando proceso de exportación semanal...")

    # 1. Definir Timestamp y nombres limpios
    timestamp_folder = datetime.now().strftime("%Y-%m-%d_%H-%M")  # Ej: 2023-10-27_19-00

    tasks = [
        {"func": load_clients, "name": "dboClientes.csv"},
        {"func": load_products, "name": "dboDestinos.csv"},
        {"func": load_orders, "name": "dboPedidos.csv"},
        {"func": load_provinces, "name": "dboProvincias.csv"},
        {"func": load_destinations, "name": "dboDestinos.csv"},
        {"func": load_order_lines, "name": "dboLineasPedido.csv"},
    ]

    # 2. Conectar a Drive
    try:
        drive_service = authenticate_drive()
    except Exception as e:
        print(f"❌ Error crítico de autenticación: {e}")
        return

    # 3) Carpeta en Google Drive
    try:
        drive_folder_id = create_drive_folder(
            drive_service, "BACKUP" + "_" + timestamp_folder, ROOT_DRIVE_FOLDER_ID
        )
    except Exception:
        return  # Si falla crear la carpeta, detenemos el proceso

    # 4. Ejecutar extracciones y subidas
    for task in tasks:
        try:
            print(f"⬇️ Procesando: {task['name']}...")
            df = task["func"]()

            if df is not None and not df.empty:
                # Ruta completa local
                file_path = paths.DATA_RAW / task["name"]

                # Guardar CSV localmente
                df.to_csv(file_path, index=False, encoding="utf-8")

                # Subir a Drive (usando el ID de la nueva carpeta creada)
                upload_file_to_drive(
                    drive_service, str(file_path), task["name"], drive_folder_id
                )

            else:
                print(f"⚠️ Dataset vacío para {task['name']}, saltando.")

        except Exception as e:
            print(f"❌ Error en tarea {task['name']}: {e}")

    # Opcional: Si quieres ahorrar espacio local, descomenta las siguientes líneas
    # para borrar la carpeta local después de subirla.
    # shutil.rmtree(local_folder_path)
    # print("🧹 Archivos temporales locales eliminados.")

    print("🏁 Proceso finalizado correctamente.")


if __name__ == "__main__":
    main()
