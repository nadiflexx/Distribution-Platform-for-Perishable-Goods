import logging
import sys

from distribution_platform.config.settings import Paths


def setup_logger(name="distribution_platform"):
    """
    Configures and returns a logger instance for the application.

    This function sets up a logger that outputs messages to both a file (execution.log)
    and the standard output (console). It ensures the logs directory exists before
    creating the file handler.

    Args:
        name (str, optional): The name of the logger. Defaults to "distribution_platform".

    Returns:
        logging.Logger: A configured logger instance ready for use.
    """
    if not Paths.LOGS.exists():
        Paths.LOGS.mkdir(parents=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(Paths.LOGS / "execution.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


log = setup_logger()
