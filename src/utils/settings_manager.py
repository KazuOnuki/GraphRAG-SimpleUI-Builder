import logging
import os

import gradio as gr
from graphrag.index.progress import PrintProgressReporter
from graphrag.prompt_tune.loader.config import read_config_parameters

from src.state.state_model import StateModel


def update_llm_settings(
    state: StateModel,
    llm_model: str,
    llm_deployment: str,
    embeddings_model: str,
    embeddings_deployment: str,
    llm_base_url: str,
    llm_api_key: str,
    embeddings_base_url: str,
    embeddings_api_key: str,
) -> StateModel:
    """
    Updates the GraphRag-related settings in the .env file and refreshes the state parameters.

    This function writes new API base URLs, keys, and model deployment information for
    both the LLM and embedding services into the `.env` file. After updating, it resets
    the environment to the initial state and reloads configuration parameters from
    settings files.

    Args:
        state (StateModel): The state object containing the initial environment
                            and configuration data.
        llm_model (str): The model name used for LLM requests.
        llm_deployment (str): The deployment name for the LLM model.
        embeddings_model (str): The model name used for embedding generation.
        embeddings_deployment (str): The deployment name for the embedding model.
        llm_base_url (str): The base URL for the LLM API.
        llm_api_key (str): The API key for accessing the LLM service.
        embeddings_base_url (str): The base URL for the embedding API.
        embeddings_api_key (str): The API key for accessing the embedding service.

    Returns:
        StateModel: The updated state object with refreshed parameters after updating
                    the .env file and reloading the environment.

    Notes:
        - This function directly modifies the `.env` file at the specified path.
        - After updating the environment variables, it resets the Python environment
            to its initial state and reloads settings from `settings.yaml` using
            `read_config_parameters`.
    """
    env_file: str = f'{os.getenv("GRAPHRAG_INPUT_BASE_DIR", "graphdata")}/.env'

    def update_env_variable(key, value, env_file):
        with open(env_file, "r") as file:
            lines: list[str] = file.readlines()
        updated: bool = False
        with open(env_file, "w") as file:
            for line in lines:
                if line.startswith(f"{key}="):
                    file.write(f"{key}={value}\n")
                    updated = True
                else:
                    file.write(line)
            if not updated:
                file.write(f"{key}={value}\n")

    # update each environ variables to .env file
    update_env_variable("GRAPHRAG_API_BASE", llm_base_url, env_file)
    update_env_variable("GRAPHRAG_API_KEY", llm_api_key, env_file)
    update_env_variable("GRAPHRAG_LLM_MODEL", llm_model, env_file)
    update_env_variable("GRAPHRAG_LLM_DEPLOYMENT_NAME", llm_deployment, env_file)
    update_env_variable(
        "GRAPHRAG_EMBEDDING_API_BASE", embeddings_base_url, env_file
    )
    update_env_variable(
        "GRAPHRAG_EMBEDDING_API_KEY", embeddings_api_key, env_file
    )
    update_env_variable("GRAPHRAG_EMBEDDING_MODEL", embeddings_model, env_file)
    update_env_variable(
        "GRAPHRAG_EMBEDDING_DEPLOYMENT_NAME", embeddings_deployment, env_file
    )

    # !reset initial environ info
    os.environ.clear()
    os.environ.update(state.initial_environ)
    print("Restored to initial state:", dict(os.environ))

    state.param = read_config_parameters(
        root="./graphdata", reporter=PrintProgressReporter("")
    )

    gr.Info("Settings have been updated successfully!")
    print("*" * 30)
    logging.info(f"param: {state.param}")
    print("*" * 30)

    return state
