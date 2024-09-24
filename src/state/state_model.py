import os
from pathlib import Path

import gradio as gr
import pandas as pd
import tiktoken
from gradio.themes.base import ThemeClass
from graphrag.config.models import GraphRagConfig
from graphrag.vector_stores.lancedb import LanceDBVectorStore


class StateModel:
    """
    A class to represent the state model for managing GraphRag/Gradio information.

    Attributes:
        initial_environ (dict[str, str] | None): Holds environment information (default: None).
        entity_df (pd.DataFrame): DataFrame to store entity information.
        relationship_df (pd.DataFrame): DataFrame to store relationship data between entities.
        text_unit_df (pd.DataFrame): DataFrame for text unit data.
        report_df (pd.DataFrame): DataFrame for report data.
        entity_embedding_df (pd.DataFrame): DataFrame for entity embeddings.
        covariate_df (pd.DataFrame): DataFrame to store covariate data.
        token_encoder (tiktoken.core.Encoding): Token encoder for text tokenization.
        description_embedding_store (LanceDBVectorStore | None): Store for description embeddings, default is None.
        timestamp (str | None): Placeholder for GraphRag reading folder name (default: None).
        param (GraphRagConfig | None): Settings from the GraphRag `settings.yaml` configuration file (default: None).
        root_dir (str): Root directory for storing graph data files (default: current working directory + "/graphdata").
        _theme (ThemeClass): Custom Gradio theme loaded from the hub.
        _css (str): Custom Gradio CSS loaded from the assets directory.
        _js (str): Custom Gradio JavaScript loaded from the assets directory.

    Methods:
        show() -> dict:
            Returns a dictionary representation of the current state model.
    """

    def __init__(self):
        self.initial_environ: dict[str, str] | None = None
        self.entity_df: pd.DataFrame = pd.DataFrame()
        self.relationship_df: pd.DataFrame = pd.DataFrame()
        self.text_unit_df: pd.DataFrame = pd.DataFrame()
        self.report_df: pd.DataFrame = pd.DataFrame()
        self.entity_embedding_df: pd.DataFrame = pd.DataFrame()
        self.covariate_df: pd.DataFrame = pd.DataFrame()
        self.token_encoder: tiktoken.core.Encoding = tiktoken.get_encoding(
            "cl100k_base"
        )
        self.description_embedding_store: LanceDBVectorStore | None = None
        self.timestamp: str | None = None
        self.param: GraphRagConfig | None = None
        self.root_dir: str = os.path.join(os.getcwd(), "graphdata")

        self._theme: ThemeClass = gr.Theme.from_hub("lone17/kotaemon")
        with (
            Path(__file__).parent.parent / "assets" / "main.css"
        ).open() as fi:
            self._css: str = fi.read()
        with (
            Path(__file__).parent.parent / "assets" / "main.js"
        ).open() as fi:
            self._js: str = fi.read()

    def show(self) -> dict:
        data = {
            "root_dir": self.root_dir,
            "relationship_df": self.relationship_df.shape,
            "text_unit_df": self.text_unit_df.shape,
            "report_df": self.report_df.shape,
            "entity_embedding_df": self.entity_embedding_df.shape,
            "covariate_df": self.covariate_df.shape,
            "token_encoder": self.token_encoder,
            "description_embedding_store": self.description_embedding_store,
            "timestamp": self.timestamp,
            "param": self.param,
            "_theme": self._theme,
            "_css": self._css,
            "_js": self._js,
        }

        return data
