import re
from datetime import datetime
from pathlib import Path

import networkx as nx
from pyvis.network import Network


class CallChainVisualizer:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    @staticmethod
    def sanitize_filename(name: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', "_", name)

    @staticmethod
    def get_node_color(label: str) -> str:
        if label.startswith("_external_") or label == "<external>":
            return "pink"
        parts = label.split("__")
        if len(parts) == 1:
            return "lightgreen"
        elif len(parts) == 2:
            if parts[1][0].isupper():
                return "red"
            else:
                return "lightblue"
        elif len(parts) >= 3:
            return "lightblue"
        elif "param" in label.lower():
            return "purple"
        return "lightgray"

    def save_file_charts(
        self,
        folder="chains_output",
        prefix="chart",
        show_external=False,
        show_sequence=True,
    ):
        """Save charts per root file with optional sequential arrows."""
        timestamp_folder = Path(folder) / datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_folder.mkdir(parents=True, exist_ok=True)

        visited_nodes = set()

        for node in self.graph.nodes:
            if node in visited_nodes:
                continue

            connected_nodes = {node}
            connected_nodes.update(nx.descendants(self.graph, node))
            connected_nodes.update(nx.ancestors(self.graph, node))

            if not show_external:
                connected_nodes = {
                    n
                    for n in connected_nodes
                    if not (
                        self.graph.nodes[n].get("label", n).startswith("_external_")
                        or self.graph.nodes[n].get("label", n) == "<external>"
                    )
                }

            if not connected_nodes:
                continue

            visited_nodes.update(connected_nodes)
            subgraph = self.graph.subgraph(connected_nodes).copy()

            first_label = self.graph.nodes[node].get("label", node)
            root_file = (
                first_label.split("__")[0] if "__" in first_label else first_label
            )
            safe_file_root = self.sanitize_filename(root_file)

            net = Network(height="800px", width="100%", directed=True)
            net.force_atlas_2based()

            # Add nodes
            for n, data in subgraph.nodes(data=True):
                label = data.get("label", n)
                color = self.get_node_color(label)
                net.add_node(n, label=label, title=label, color=color)

            # Add normal edges
            for src, dst, data in subgraph.edges(data=True):
                if src in subgraph and dst in subgraph:
                    net.add_edge(src, dst, title=data.get("file", ""))

            # Add sequential workflow edges (a -> b -> c)
            if show_sequence:
                # Get nodes in DFS order starting from the entry node
                dfs_nodes = list(nx.dfs_preorder_nodes(subgraph, source=node))
                for i in range(len(dfs_nodes) - 1):
                    src, dst = dfs_nodes[i], dfs_nodes[i + 1]
                    net.add_edge(src, dst, color="orange", width=2, title="sequence")

            filename = timestamp_folder / f"{prefix}_{safe_file_root}.html"
            net.write_html(str(filename))
            print(f"[OK] Saved file chart for {root_file} → {filename}")
