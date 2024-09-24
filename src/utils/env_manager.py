import copy
import os

from src.state.state_model import StateModel


def save_initial_environ(state: StateModel) -> None:
    """save initial env info to gradio state

    Args:
        state (StateModel): A class to represent the state model for managing graphrag/gradio information.
    """
    state.initial_environ = copy.deepcopy(os.environ)
