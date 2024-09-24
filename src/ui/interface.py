import logging
import os

import gradio as gr
from gradio.blocks import Blocks
from gradio.components.base import Component, FormComponent

from src.search.search_engine import send_message
from src.state.state_model import StateModel
from src.utils.blob_storage import download_idx_from_storage
from src.utils.settings_manager import update_llm_settings


def create_gradio_interface(state: StateModel) -> Blocks:
    """
    Creates a Gradio interface for the MS Hackathon 2024 Demo App.

    This function builds the user interface with multiple tabs, including a chat system,
    settings panels for environment variables and GraphRAG index settings, and options
    for selecting search types and response formats. The interface is built using Gradio's
    `Blocks`, `Tab`, `Column`, and other components, with integration for LLM settings
    and a chatbot.

    Args:
        state (StateModel): The current state of the application, containing the theme,
                            CSS, JavaScript, and other configuration data.

    Returns:
        Blocks: The Gradio Blocks instance representing the full UI interface.

    Functionality:
        - Chat tab: Enables conversation with GraphRag-powered agents, supports selecting
                    response formats, community level, and more.
        - Settings tab: Provides settings for API keys, model selection, and storage
                        connection for GraphRAG index settings.
        - Shift+Enter support: Allows submitting queries via keyboard.
        - Dynamic loading of settings and updates to environment variables.
    """
    with gr.Blocks(
        theme=state._theme,
        css=state._css,
        js=state._js,
        title="MS Hackathon 2024 Demo App",
    ) as demo:
        state: FormComponent = gr.State(state)
        logging.info(f"initial state show: {state.value.show()}")

        with gr.Tabs():
            with gr.Tab("Chat", elem_id="chat-tab"):
                with gr.Row():
                    with gr.Column(scale=1, elem_id="conv-settings-panel"):
                        with gr.Accordion("GraphRAG Parameter", open=True):
                            query_type: FormComponent = gr.Radio(
                                ["global", "local"],
                                label="Query Type",
                                value="global",
                                info="Global: community-based search, Local: entity-based search",
                            )
                            selected_folder: FormComponent = gr.Dropdown(
                                label="Select Index Folder to Chat With",
                                choices=list_output_folders(
                                    state.value.root_dir
                                ),
                                value=state.value.timestamp,
                                interactive=True,
                            )

                            with gr.Group(visible=True) as _:
                                community_level: FormComponent = gr.Slider(
                                    label="Community Level",
                                    minimum=1,
                                    maximum=10,
                                    value=2,
                                    step=1,
                                    info="Higher values use reports on smaller communities",
                                )
                                response_type: FormComponent = gr.Dropdown(
                                    label="Response Type",
                                    choices=[
                                        "Multiple Paragraphs",
                                        "Single Paragraph",
                                        "Single Sentence",
                                        "List of 3-7 Points",
                                        "Single Page",
                                        "Multi-Page Report",
                                    ],
                                    value="Multiple Paragraphs",
                                    info="Specify the desired format of the response",
                                )

                    with gr.Column(scale=5, elem_id="chat-area"):
                        chatbot: Component = gr.Chatbot(
                            label="Global Hack",
                            placeholder="""This is the beginning of a new conversation.\nMake sure to have added a LLM by following the instructions in the Help tab.""",
                            show_label=False,
                            elem_id="main-chat-bot",
                            show_copy_button=True,
                            likeable=True,
                            bubble_full_width=False,
                        )
                        with gr.Row():
                            query_input: FormComponent = gr.Text(
                                placeholder="Chat input",
                                scale=15,
                                container=False,
                                max_lines=10,
                            )
                            clear_chat_btn: Component = gr.Button(
                                "Clear Chat", variant="secondary"
                            )

                    with gr.Column(scale=5, elem_id="chat-info-panel"):
                        with gr.Accordion(
                            label="Information panel", open=True
                        ) as _:
                            with gr.Accordion(
                                label="Relationship Plot", open=False
                            ) as _:
                                plot_panel: Component = gr.Plot(visible=True)
                            with gr.Accordion(
                                label="Entity Table", open=False
                            ) as _:
                                entity_html_display: Component = gr.HTML()
                            with gr.Accordion(
                                label="Relationship Table", open=False
                            ) as _:
                                relationship_html_display: Component = (
                                    gr.HTML()
                                )
                            with gr.Accordion(
                                label="Source Table", open=False
                            ) as _:
                                source_html_display: Component = gr.HTML()
                            with gr.Accordion(
                                label="Report Table", open=True
                            ) as _:
                                report_html_display: Component = gr.HTML()

            with gr.Tab(
                "Settings",
                visible=True,
                elem_id="settings-tab",
                elem_classes=["fill-main-area-height", "scrollable"],
            ):
                with gr.Tab("ENV Settings"):
                    llm_base_url: FormComponent = gr.Textbox(
                        label="GRAPHRAG_API_BASE",
                        value=state.value.param.llm.api_base,
                    )
                    llm_api_key: FormComponent = gr.Textbox(
                        label="GRAPHRAG_API_KEY",
                        value=state.value.param.llm.api_key,
                        type="password",
                    )
                    llm_model: FormComponent = gr.Textbox(
                        label="GRAPHRAG_LLM_MODEL",
                        value=state.value.param.llm.model,
                    )
                    llm_deployment: FormComponent = gr.Textbox(
                        label="GRAPHRAG_LLM_DEPLOYMENT",
                        value=state.value.param.llm.deployment_name,
                    )
                    embeddings_base_url: FormComponent = gr.Textbox(
                        label="GRAPHRAG_EMBEDDING_API_BASE",
                        value=state.value.param.embeddings.llm.api_base,
                    )
                    embeddings_api_key: FormComponent = gr.Textbox(
                        label="GRAPHRAG_EMBEDDING_API_KEY",
                        value=state.value.param.embeddings.llm.api_key,
                        type="password",
                    )
                    embeddings_model: FormComponent = gr.Textbox(
                        label="GRAPHRAG_EMBEDDING_MODEL",
                        value=state.value.param.embeddings.llm.model,
                    )
                    embeddings_deployment: FormComponent = gr.Textbox(
                        label="GRAPHRAG_EMBEDDING_DEPLOYMENT",
                        value=state.value.param.embeddings.llm.deployment_name,
                    )

                    update_settings_btn: Component = gr.Button(
                        "Update .env Settings", variant="primary"
                    )
                    update_settings_btn.click(
                        fn=update_llm_settings,
                        inputs=[
                            state,
                            llm_model,
                            llm_deployment,
                            embeddings_model,
                            embeddings_deployment,
                            llm_base_url,
                            llm_api_key,
                            embeddings_base_url,
                            embeddings_api_key,
                        ],
                        outputs=[state],
                    )
                with gr.Tab("GraphRAG Index Settings"):
                    storage_connection_str: FormComponent = gr.Textbox(
                        label="GRAPHRAG_STORAGE_CONNECTION_STRING",
                        value=state.value.param.storage.connection_string,
                        type="password",
                    )
                    storage_container_name: FormComponent = gr.Textbox(
                        label="CONTAINER_NAME",
                        value=state.value.param.storage.container_name,
                    )
                    download_idx_btn: Component = gr.Button(
                        "Download Index from Above Storage", variant="primary"
                    )
                    download_idx_btn.click(
                        fn=download_idx_from_storage,
                        inputs=[
                            state,
                            storage_connection_str,
                            storage_container_name,
                        ],
                        outputs=[state],
                    )

        clear_chat_btn.click(
            fn=lambda: ([], ""), outputs=[chatbot, query_input]
        )

        query_input.submit(
            fn=send_message,
            inputs=[
                state,
                query_type,
                query_input,
                chatbot,
                community_level,
                response_type,
                selected_folder,
            ],
            # html display ver
            outputs=[
                state,
                chatbot,
                query_input,
                entity_html_display,
                relationship_html_display,
                source_html_display,
                report_html_display,
                plot_panel,
            ],
        )

        # Add this JavaScript to enable Shift+Enter functionality
        demo.load(
            js="""
                function addShiftEnterListener() {
                    const queryInput = document.getElementById('query-input');
                    if (queryInput) {
                    queryInput.addEventListener('keydown', function(event) {
                        if (event.key === 'Enter' && event.shiftKey) {
                        event.preventDefault();
                        const submitButton = queryInput.closest('.gradio-container').querySelector('button.primary');
                        if (submitButton) {
                            submitButton.click();
                        }
                        }
                    });
                    }
                }
                document.addEventListener('DOMContentLoaded', addShiftEnterListener);
            """
        )

    return demo.queue()


def list_output_folders(root_dir: str) -> list:
    """
    Lists the output folders from the specified root directory.

    This function scans the "output" directory inside the specified root directory
    and returns a list of folder names sorted in reverse chronological order.

    Args:
        root_dir (str): The root directory where the output folders are stored.

    Returns:
        list: A list of folder names found in the "output" directory, sorted in reverse order.
    """
    output_dir: str = os.path.join(root_dir, "output")
    folders: list = [
        f
        for f in os.listdir(output_dir)
        if os.path.isdir(os.path.join(output_dir, f))
    ]
    return sorted(folders, reverse=True)
