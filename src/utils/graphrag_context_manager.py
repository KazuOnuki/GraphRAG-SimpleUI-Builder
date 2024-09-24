import logging
import os

from graphrag.model.community_report import CommunityReport
from graphrag.model.covariate import Covariate
from graphrag.model.entity import Entity
from graphrag.model.relationship import Relationship
from graphrag.model.text_unit import TextUnit
from graphrag.query.context_builder.builders import (
    GlobalContextBuilder,
    LocalContextBuilder,
)
from graphrag.query.context_builder.entity_extraction import (
    EntityVectorStoreKey,
)
from graphrag.query.indexer_adapters import (
    read_indexer_covariates,
    read_indexer_entities,
    read_indexer_relationships,
    read_indexer_reports,
    read_indexer_text_units,
)
from graphrag.query.input.loaders.dfs import store_entity_semantic_embeddings
from graphrag.query.llm.oai.embedding import OpenAIEmbedding
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.structured_search.global_search.community_context import (
    GlobalCommunityContext,
)
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)
from graphrag.vector_stores import BaseVectorStore

from src.state.state_model import StateModel
from src.utils.df_manager import read_df


def get_context_builder(
    state: StateModel,
    query_type: str,
    community_level: str,
    selected_folder: str,
) -> GlobalContextBuilder | LocalContextBuilder:
    """
    Builds and returns a context builder based on the specified query type and
    community level, initializing it with relevant data from the state.

    This function selects between a global or local context builder based on the
    `query_type` parameter. It reads necessary data from the specified folder
    and initializes the context with reports, entities, relationships, text units,
    and covariates as appropriate.

    Args:
        state (StateModel): The state object containing dataframes and parameters
                            needed for context building.
        query_type (str): The type of query to perform. Can be either "global"
                            for community-based queries or "local" for entity-based
                            queries.
        community_level (str): The level of community to query, which influences
                                the selection of reports and entities.
        selected_folder (str): The folder containing output data to read from.
                                If different from the current state, the folder is updated.

    Returns:
        context_builder (GlobalContextBuilder | LocalContextBuilder): An instance of the context builder
                                                                        corresponding to the specified query
                                                                        type, initialized with relevant data.

    Raises:
        Exception: Logs errors and raises exceptions if data reading or context
                    building fails.

    Notes:
        - The function modifies the state timestamp to reflect the currently selected
            folder.
        - If the selected folder is not the same as the current timestamp, it
            re-reads the dataframe from the artifacts folder associated with the
            selected folder.
    """
    root_dir: str = f"{state.root_dir}/output"
    logging.info(f"current selected_folder: {selected_folder}")
    logging.info(f"selected folder before this call: {state.timestamp}")

    # *read dataframe again if user selecte other graphrag output folder
    if (selected_folder != None) and (selected_folder != state.timestamp):
        selected_folder: str = os.path.join(root_dir, selected_folder)
        artifacts_folder: str = os.path.join(selected_folder, "artifacts")
        read_df(artifacts_folder, state)
        state.timestamp = selected_folder

    api_key: str = state.param.embeddings.llm.api_key
    llm_model: str = state.param.embeddings.llm.model
    llm_deployment: str = state.param.embeddings.llm.deployment_name
    api_base: str = state.param.embeddings.llm.api_base
    api_version: str = state.param.embeddings.llm.api_version

    try:
        if query_type == "global":
            reports: list[CommunityReport] = read_indexer_reports(
                state.report_df, state.entity_df, community_level
            )
            entities: list[Entity] = read_indexer_entities(
                state.entity_df, state.entity_embedding_df, community_level
            )
            context_builder: GlobalContextBuilder = GlobalCommunityContext(
                community_reports=reports,
                entities=entities,
                token_encoder=state.token_encoder,
            )
            return context_builder

        elif query_type == "local":
            reports: list[CommunityReport] = read_indexer_reports(
                state.report_df, state.entity_df, community_level
            )
            text_units: list[TextUnit] = read_indexer_text_units(
                state.text_unit_df
            )

            # *integrate entity_df and entitiy_embedding_df
            entities: list[Entity] = read_indexer_entities(
                state.entity_df, state.entity_embedding_df, community_level
            )
            # !load description embeddings to an in-memory lancedb vectorstore
            entity_description_embeddings: BaseVectorStore = (
                store_entity_semantic_embeddings(
                    entities=entities,
                    vectorstore=state.description_embedding_store,
                )
            )

            relationships: list[Relationship] = read_indexer_relationships(
                state.relationship_df
            )
            if state.covariate_df.empty:
                covariates = None
            else:
                claims: list[Covariate] = read_indexer_covariates(
                    state.covariate_df
                )
                covariates: dict = {"claims": claims}

            text_embedder: OpenAIEmbedding = OpenAIEmbedding(
                api_key=api_key,
                api_base=api_base,
                api_version=api_version,
                api_type=OpenaiApiType.AzureOpenAI,
                model=llm_model,
                deployment_name=llm_deployment,
                max_retries=20,
            )

            context_builder: LocalContextBuilder = LocalSearchMixedContext(
                community_reports=reports,  # ! things to summarize entity/relationthip
                text_units=text_units,
                entities=entities,  # ! entity type (human / organization etc) list
                relationships=relationships,
                covariates=covariates,
                entity_text_embeddings=state.description_embedding_store,
                embedding_vectorstore_key=EntityVectorStoreKey.ID,
                text_embedder=text_embedder,
                token_encoder=state.token_encoder,
            )
            return context_builder

    except Exception as e:
        logging.error(f"error: {e}")
        import traceback

        traceback.print_exc()
