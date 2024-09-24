from gradio.blocks import Blocks

from src.config.config_loader import initialize_data
from src.state.state_model import StateModel
from src.ui.interface import create_gradio_interface
from src.utils.env_manager import save_initial_environ
from src.utils.logging_manager import setup_logging, suppress_warnings

if __name__ == "__main__":
    suppress_warnings()
    setup_logging()

    # !Set Gradio-State Init
    state: StateModel = StateModel()
    # !save initial env info to gradio state
    save_initial_environ(state)
    # !Initializes the data within the provided StateModel instance.
    initialize_data(state)
    # !Create UI Component
    demo: Blocks = create_gradio_interface(state)
    # !Start UI defined by above Blocks
    demo.launch(server_port=7859, share=False)
