import logging
import os
from datetime import datetime

from graphrag.index.progress import PrintProgressReporter
from graphrag.prompt_tune.loader.config import read_config_parameters
from graphrag.vector_stores.lancedb import LanceDBVectorStore

from src.state.state_model import StateModel
from src.utils.df_manager import read_df


def initialize_data(state: StateModel) -> None:
    """
    Initializes the data within the provided `StateModel` instance.

    This function retrieves the latest output folder from the `StateModel`, reads data from the folder,
    sets up a connection to a LanceDB vector store, and loads configuration parameters from a settings file.
    If any error occurs during the initialization process, it is logged.

    Args:
        state (StateModel): The `StateModel` instance that holds the application state and data.

    Raises:
        Exception: Any exceptions that occur during initialization are logged as errors.

    Process:
        1. Finds the latest output folder and updates the `state.timestamp`.
        2. Reads relevant DataFrames from the `artifacts` folder and updates the `StateModel`.
        3. Initializes the `LanceDBVectorStore` for storing graphrag entity description embeddings.
        4. Loads configuration parameters from the root directory's `settings.yaml`.
    """
    try:
        # *Annotate as tuple
        output: tuple[str, str] = find_latest_output_folder(
            state
        )  # Annotate as tuple
        latest_output_folder, timestamp = output

        state.timestamp = timestamp
        artifacts_folder: str = os.path.join(latest_output_folder, "artifacts")
        read_df(artifacts_folder, state)

        LANCEDB_URI: str = f"{artifacts_folder}/lancedb"
        state.description_embedding_store = LanceDBVectorStore(
            collection_name="entity_description_embeddings",
        )
        state.description_embedding_store.connect(db_uri=LANCEDB_URI)

        # Note: read from .env and settings.yaml at same root dir.
        state.param = read_config_parameters(
            root=state.root_dir, reporter=PrintProgressReporter("")
        )

    except Exception as e:
        logging.error(f"Error initializing data: {str(e)}")


def find_latest_output_folder(state: StateModel) -> tuple[str, str]:
    """Finds the latest output folder from the 'output' directory in the given StateModel instance.

    This function searches for the latest folder based on the creation time from the 'output'
    directory inside the `state.root_dir`. It assumes that the folder names follow a timestamp format
    (`"%Y%m%d-%H%M%S"`) and returns the path of the latest valid folder.

    Args:
        state (StateModel): The StateModel instance managing the root directory and other related data.

    Raises:
        ValueError: If no output folders are found in the directory.
        ValueError: If no folders with valid timestamp names are found.
        ValueError: If the 'artifacts' subfolder is missing from the latest valid output folder.

    Returns:
        Tuple[str, str]:
            A tuple containing:
            - The path of the latest output folder (str).
            - The name of the latest output folder (str).
    """
    # !graphrag Index output folder list
    folders: list = [
        f
        for f in os.listdir(os.path.join(state.root_dir, "output"))
        if os.path.isdir(os.path.join(state.root_dir, "output", f))
    ]
    if not folders:
        raise ValueError("No output folders found")
    # Sort folders by creation time, most recent first
    sorted_folders: list = sorted(
        folders,
        key=lambda x: os.path.getctime(
            os.path.join(state.root_dir, "output", x)
        ),
        reverse=True,
    )
    latest_folder: str | None = None
    for folder in sorted_folders:
        try:
            # !Try to parse the folder name as a timestamp (graphrag index output's format is "%Y%m%d-%H%M%S")
            datetime.strptime(folder, "%Y%m%d-%H%M%S")
            latest_folder = folder
            break
        except ValueError:
            continue
    if latest_folder is None:
        raise ValueError("No valid timestamp folders found")
    latest_path = os.path.join(state.root_dir, "output", latest_folder)
    artifacts_path = os.path.join(latest_path, "artifacts")
    if not os.path.exists(artifacts_path):
        raise ValueError(f"Artifacts folder not found in {latest_path}")
    return latest_path, latest_folder
