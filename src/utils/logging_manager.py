import logging
import os
import warnings


def suppress_warnings() -> None:
    """Function to ignore warning from gradio_client.documentation"""
    warnings.filterwarnings(
        "ignore", category=UserWarning, module="gradio_client.documentation"
    )


def setup_logging(level: str = "INFO") -> None:
    """Function to control logging level and log format

    Args:
        level (str, optional): log level (INFO/WARNING/ERROR/DEBUG/CRITICAL) to display. Defaults to "INFO".
    """
    level_dict = {
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "DEBUG": logging.DEBUG,
        "CRITICAL": logging.CRITICAL,
    }
    # !Default is INFO
    logging_level = level_dict.get(level.upper(), logging.INFO)

    logging.basicConfig(
        level=logging_level,
        format="🚀 [%(asctime)s] [%(levelname)s] 🚀 =>  %(message)s",
    )
