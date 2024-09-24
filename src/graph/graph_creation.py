import networkx as nx
import pandas as pd


def create_knowledge_graph(df: pd.DataFrame) -> nx.Graph:
    """
    Creates a knowledge graph from a DataFrame containing source-target relationships.

    This function constructs a graph where each row in the DataFrame represents
    an edge between a source node and a target node. Additional attributes from
    the DataFrame are added to the edges.

    Args:
        df (pd.DataFrame): A DataFrame containing at least two columns:
                            'source' and 'target'. Additional columns are treated
                            as edge attributes.

    Returns:
        nx.Graph: A NetworkX graph object representing the knowledge graph,
                    with edges corresponding to the rows of the DataFrame and
                    attributes set as specified in the DataFrame.

    Raises:
        KeyError: If the DataFrame does not contain the required 'source'
                    or 'target' columns.
    """
    G: nx.Graph = nx.Graph()
    for _, row in df.iterrows():
        source = row["source"]
        target = row["target"]
        attributes = {
            k: v for k, v in row.items() if k not in ["source", "target"]
        }
        G.add_edge(source, target, **attributes)
    return G
