import glob
import logging
import os

import pandas as pd

from src.state.state_model import StateModel


def read_df(artifacts_folder: str, state: StateModel):
    """
    Reads data from Parquet files located in the specified 'artifacts' folder and stores it in global DataFrames.

    Args:
        artifacts_folder (str): The folder path where the data files are stored.

    Globals:
        entity_df (pd.DataFrame): DataFrame for entity data.
        relationship_df (pd.DataFrame): DataFrame for relationship data.
        text_unit_df (pd.DataFrame): DataFrame for text unit data.
        report_df (pd.DataFrame): DataFrame for report data.
        entity_embedding_df (pd.DataFrame): DataFrame for entity embedding data.
        covariate_df (pd.DataFrame): DataFrame for covariate data.
    """
    tables = {
        "entity_df": "create_final_nodes",
        "relationship_df": "create_final_relationships",
        "text_unit_df": "create_final_text_units",
        "report_df": "create_final_community_reports",
        "entity_embedding_df": "create_final_entities",
        "covariate_df": "create_final_covariates",
    }

    for df_name, file_prefix in tables.items():
        file_pattern = os.path.join(
            artifacts_folder, f"{file_prefix}*.parquet"
        )
        matching_files = glob.glob(file_pattern)
        if matching_files:
            latest_file = max(matching_files, key=os.path.getctime)
            df = pd.read_parquet(latest_file)
            if df_name == "entity_df":
                state.entity_df = df
            if df_name == "relationship_df":
                state.relationship_df = df
            if df_name == "text_unit_df":
                state.text_unit_df = df
            if df_name == "report_df":
                state.report_df = df
            if df_name == "entity_embedding_df":
                state.entity_embedding_df = df
            if df_name == "covariate_df":
                state.covariate_df = df

            # globals()[df_name] = df
            logging.info(f"Successfully loaded {df_name} from {latest_file}")
        else:
            logging.warning(
                f"No matching file found for {df_name} in {artifacts_folder}. Initializing as an empty DataFrame."
            )
