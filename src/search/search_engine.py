import logging
import re
from typing import Literal, LiteralString

import networkx as nx
import pandas as pd
from graphrag.query.context_builder.builders import (
    GlobalContextBuilder,
    LocalContextBuilder,
)
from graphrag.query.context_builder.entity_extraction import (
    EntityVectorStoreKey,
)
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.structured_search.base import BaseSearch, SearchResult
from graphrag.query.structured_search.global_search.search import GlobalSearch
from graphrag.query.structured_search.local_search.search import LocalSearch
from plotly.basedatatypes import BaseFigure

from src.graph.graph_creation import create_knowledge_graph
from src.graph.graph_visualization import visualize_graph
from src.state.state_model import StateModel
from src.utils.graphrag_context_manager import get_context_builder


async def send_message(
    state: StateModel,
    query_type: str,
    query: str,
    history: list,
    community_level: str,
    response_type: str,
    selected_folder: str,
) -> (
    tuple[
        StateModel,
        list,
        str,
        Literal["<p>No Entities due to Global Search</p>"],
        Literal["<p>No Relationship due to Global Search</p>"],
        Literal["<p>No Source due to Global Search</p>"],
        str,
        None,
    ]
    | tuple[
        StateModel,
        list,
        str,
        str | LiteralString,
        str | LiteralString,
        str | LiteralString,
        str | LiteralString,
        BaseFigure | None,
    ]
    | tuple[
        StateModel,
        list,
        str,
        Literal["<p>No Entities</p>"],
        Literal["<p>No Relationship</p>"],
        Literal["<p>No Source</p>"],
        Literal["<p>No Report</p>"],
        None,
    ]
):
    """
    Sends a query to a language model and retrieves the corresponding response
    along with contextual information.

    This function handles both global and local queries by interacting with
    different search engines based on the specified query type. It constructs
    context builders, processes the search results, and prepares the
    display outputs for entities, relationships, sources, and reports.

    Args:
        state (StateModel): The current state of the application, containing
                            parameters and context for the query.
        query_type (str): The type of query ('global' or 'local') that determines
                                the search method to use.
        query (str): The user's input query to be processed.
        history (list): A list of previous queries and responses for tracking
                        conversation history.
        community_level (str): The level of community context to be considered
                                in the search.
        response_type (str): The expected format and type of the response.
        selected_folder (str): The folder from which to read the output data.

    Returns:
        tuple: A tuple containing:
            - state (StateModel): Updated state after processing the query.
            - history (list): Updated history including the new query and response.
            - str: An empty string (placeholder).
            - str: HTML formatted string for entity display.
            - str: HTML formatted string for relationship display.
            - str: HTML formatted string for source display.
            - str: HTML formatted string for report display.
            - BaseFigure or None: A plotly figure for visualizing the graph, or None
                                    if no relationships were found.

    Raises:
        Exception: Logs any exceptions that occur during the processing of the query.
    """
    logging.info(f"query_type: {query_type}")
    logging.info(f"community_level: {community_level}")
    logging.info(f"response_type: {response_type}")
    logging.info(f"param: {state.param}")

    api_key: str | None = state.param.llm.api_key
    llm_model: str = state.param.llm.model
    llm_deployment: str | None = state.param.llm.deployment_name
    api_base: str | None = state.param.llm.api_base
    api_version: str | None = state.param.llm.api_version

    llm: ChatOpenAI = ChatOpenAI(
        api_key=api_key,
        model=llm_model,
        deployment_name=llm_deployment,
        api_base=api_base,
        api_version=api_version,
        api_type=OpenaiApiType.AzureOpenAI,
        max_retries=10,
    )

    # !get GraphRag Search context Builder
    context_builder: GlobalContextBuilder | LocalContextBuilder = (
        get_context_builder(
            state, query_type, community_level, selected_folder
        )
    )

    try:
        if query_type == "global":

            context_builder_params: dict = {
                "use_community_summary": False,  # !False means using full community reports. True means using community short summaries.
                "shuffle_data": True,
                "include_community_rank": True,
                "min_community_rank": 0,
                "community_rank_name": "rank",
                "include_community_weight": True,
                "community_weight_name": "occurrence weight",
                "normalize_community_weight": True,
                "max_tokens": 2000,  # !change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
                "context_name": "Reports",
            }

            map_llm_params: dict = {
                "max_tokens": 1000,
                "temperature": 0.0,
            }

            reduce_llm_params: dict = {
                "max_tokens": 1000,  # !change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000-1500)
                "temperature": 0.0,
            }

            search_engine: BaseSearch = GlobalSearch(
                llm=llm,
                context_builder=context_builder,
                token_encoder=state.token_encoder,
                max_data_tokens=2000,  # !change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
                map_llm_params=map_llm_params,
                reduce_llm_params=reduce_llm_params,
                allow_general_knowledge=False,  # !set this to True will add instruction to encourage the LLM to incorporate general knowledge in the response, which may increase hallucinations, but could be useful in some use cases.
                json_mode=False,  # !set this to False if your LLM model does not support JSON mode.
                context_builder_params=context_builder_params,
                concurrent_coroutines=32,
                response_type=f"{response_type}",  # !free form text describing the response type and format, can be anything, e.g. prioritized list, single paragraph, multiple paragraphs, multiple-page report
            )

            result: SearchResult = await search_engine.asearch(query)

            df: pd.DataFrame = result.context_data["reports"]
            # !extract Reports[xx]
            ids: list[str] = re.findall(
                r"Reports\s*\(([\d,\s]*)", result.response
            )
            all_ids: list = []
            for id_group in ids:
                all_ids.extend(
                    [
                        str(id.strip())
                        for id in id_group.split(",")
                        if id.strip()
                    ]
                )
            # !extract df from related Report
            related_df: pd.DataFrame = df[df["id"].isin(all_ids)]
            report_html_display: str = (
                related_df.to_html(index=False)
                if not related_df.empty
                else "<p>No Data Available</p>"
            )
            history.append((query, result.response))

            return (
                state,
                history,
                str(""),
                "<p>No Entities due to Global Search</p>",
                "<p>No Relationship due to Global Search</p>",
                "<p>No Source due to Global Search</p>",
                report_html_display,
                None,
            )

        elif query_type == "local":
            local_context_params: dict = {
                "text_unit_prop": 0.5,
                "community_prop": 0.1,
                "conversation_history_max_turns": 5,
                "conversation_history_user_turns_only": True,
                "top_k_mapped_entities": 10,
                "top_k_relationships": 10,
                "include_entity_rank": False,
                "include_relationship_weight": False,
                "include_community_rank": False,
                "return_candidate_context": False,
                "embedding_vectorstore_key": EntityVectorStoreKey.ID,
                "max_tokens": 3000,  # !change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
            }
            llm_params: dict = {
                "max_tokens": 1000,  # !change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000=1500)
                "temperature": 0.0,
            }

            search_engine: BaseSearch = LocalSearch(
                llm=llm,
                context_builder=context_builder,
                token_encoder=state.token_encoder,
                llm_params=llm_params,
                context_builder_params=local_context_params,
                response_type=f"{response_type}",  # !free form text describing the response type and format, can be anything, e.g. prioritized list, single paragraph, multiple paragraphs, multiple-page report
            )

            result: SearchResult = await search_engine.asearch(query)
            context_records: dict[str, pd.DataFrame] = result.context_data
            entities: pd.DataFrame = context_records.get(
                "entities", pd.DataFrame()
            )
            relationships: pd.DataFrame = context_records.get(
                "relationships", pd.DataFrame()
            )
            reports: pd.DataFrame = context_records.get(
                "reports", pd.DataFrame()
            )
            sources: pd.DataFrame = context_records.get(
                "sources", pd.DataFrame()
            )

            entity_html_display: str = ""
            if not entities.empty:
                entity_html_display += entities[
                    ["entity", "description"]
                ].to_html(index=False)
            else:
                entity_html_display += f"\n\n<h5>No Entities found</h5>"

            relationship_html_display: str = ""
            if not relationships.empty:
                relationship_html_display += relationships[
                    ["source", "target", "description"]
                ].to_html(index=False)
            else:
                relationship_html_display += (
                    f"\n\n<h5>No Relationships found</h5>"
                )

            source_html_display: str = ""
            if not sources.empty:
                for _, row in sources.iterrows():
                    output: tuple[str, str] = row["id"], row["text"]
                    title, content = output
                    source_html_display += (
                        f"\n\n<h5>Source <b>#{title}</b></h5>\n"
                    )
                    source_html_display += content
            else:
                source_html_display += f"\n\n<h5>No Sources found</h5>"

            report_html_display: str = ""
            if not reports.empty:
                for _, row in reports.iterrows():
                    output: tuple[str, str] = row["title"], row["content"]
                    title, content = output
                    report_html_display += (
                        f"\n\n<h5>Report <b>{title}</b></h5>\n"
                    )
                    report_html_display += content
            else:
                report_html_display += f"\n\n<h5>No Report found</h5>"

            history.append((query, result.response))

            # !Plog GraphRag Graph Visualization
            if not relationships.empty:
                G: nx.Graph = create_knowledge_graph(relationships)
                plot_panel: BaseFigure = visualize_graph(G)
            else:
                plot_panel: None | BaseFigure = None

            return (
                state,
                history,
                str(""),
                entity_html_display,
                relationship_html_display,
                source_html_display,
                report_html_display,
                plot_panel,
            )

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        logging.error(error_message)
        logging.exception("Exception details:")
        history.append((query, error_message))

    return (
        state,
        history,
        str(""),
        "<p>No Entities</p>",
        "<p>No Relationship</p>",
        "<p>No Source</p>",
        "<p>No Report</p>",
        None,
    )
