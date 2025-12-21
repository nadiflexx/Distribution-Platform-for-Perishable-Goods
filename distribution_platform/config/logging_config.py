import logging
import sys

from distribution_platform.config.settings import Paths


def setup_logger(name="distribution_platform"):
    # Crear carpeta de logs si no existe
    if not Paths.LOGS.exists():
        Paths.LOGS.mkdir(parents=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Formato del log: [FECHA] [NIVEL] Mensaje
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler 1: Archivo (guarda todo)
    file_handler = logging.FileHandler(Paths.LOGS / "execution.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler 2: Consola (para ver en vivo)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Instancia global del logger
log = setup_logger()
