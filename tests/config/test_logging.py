import logging
from unittest.mock import patch

from distribution_platform.config.logging_config import setup_logger


@patch("distribution_platform.config.logging_config.Paths")
@patch("logging.FileHandler")
def test_setup_logger(mock_file_handler, mock_paths):
    """Prueba la configuración del logger."""

    mock_paths.LOGS.exists.return_value = False

    logger = setup_logger("test_logger_setup")

    mock_paths.LOGS.mkdir.assert_called_once_with(parents=True)

    mock_file_handler.assert_called_once()

    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger_setup"
    assert logger.level == logging.INFO

    assert len(logger.handlers) == 2

    logger.handlers = []
