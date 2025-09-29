import colorsys
import json
import re
from datetime import datetime
from pathlib import Path

import networkx as nx
from pyvis.network import Network


class CallChainVisualizer:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    # -------------------- UTIL --------------------
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

    # -------------------- BUILDERS --------------------
    def _build_subgraph(self, nodes, show_external):
        subgraph_nodes = set()
        for node in nodes:
            subgraph_nodes.add(node)
            subgraph_nodes.update(nx.descendants(self.graph, node))
            subgraph_nodes.update(nx.ancestors(self.graph, node))
        if not show_external:
            subgraph_nodes = {
                n
                for n in subgraph_nodes
                if not (
                    self.graph.nodes[n].get("label", n).startswith("_external_")
                    or self.graph.nodes[n].get("label", n) == "<external>"
                )
            }
        if not subgraph_nodes:
            return None
        return self.graph.subgraph(subgraph_nodes).copy()

    # -------------------- NETWORK --------------------
    def _create_network(self, hierarchical=False):
        net = Network(height="100%", width="100%", directed=True, notebook=True)
        base_options = {
            "interaction": {"dragNodes": True},
            "physics": {
                "enabled": False,
                "stabilization": {"enabled": True},
                "solver": "forceAtlas2Based",
            },
        }
        if hierarchical:
            max_len = max(
                (
                    len(data.get("label", str(n)))
                    for n, data in self.graph.nodes(data=True)
                ),
                default=10,
            )
            horizontal_spacing = max(20, max_len * 10)
            hier_opts = {
                "layout": {
                    "hierarchical": {
                        "enabled": True,
                        "levelSeparation": 180,
                        "nodeSpacing": horizontal_spacing,
                        "treeSpacing": 400,
                        "direction": "UD",
                        "sortMethod": "directed",
                    }
                }
            }
            base_options.update(hier_opts)
        net.set_options(json.dumps(base_options))
        return net

    # -------------------- ADD NODES --------------------
    def _add_nodes(self, net, subgraph):
        for n, data in subgraph.nodes(data=True):
            label = data.get("label", n)
            color = self.get_node_color(label)
            group = label.split("__")[0] if "__" in label else label
            net.add_node(
                n,
                label=label,
                title=label,
                color=color,
                group=group,
                physics=False,
                fixed=False,
            )

    # -------------------- DUPLICATE TREE --------------------
    def _add_duplicate_tree(self, net, subgraph, is_gray=True):
        """
        Duplicate nodes for either gray tree or workflow-style edges.
        Each root gets its own duplicate sequence to avoid collisions.
        """
        all_nodes = list(subgraph.nodes)
        x_offset = 300
        y_spacing = 160

        def is_helper(label: str) -> bool:
            return (
                label.startswith("__")
                or label.startswith("_external_")
                or label == "<external>"
            )

        # find roots (nodes with no in-edges) for this tree
        roots = [n for n in all_nodes if subgraph.in_degree(n) == 0]

        dup_map_global = {}  # maps (node, root) -> duplicate id

        for root_idx, root in enumerate(roots):
            reachable = nx.descendants(subgraph, root) | {root}
            topo_nodes = list(nx.topological_sort(subgraph.subgraph(reachable)))
            for idx, node in enumerate(topo_nodes):
                dup_type = "gray" if is_gray else "wf"
                dup_id = f"{node}__{dup_type}{root_idx}"
                dup_map_global[(node, root)] = dup_id
                net.add_node(
                    dup_id,
                    label=subgraph.nodes[node].get("label", node),
                    title=subgraph.nodes[node].get("label", node),
                    color=self.get_node_color(subgraph.nodes[node].get("label", node)),
                    x=(
                        root_idx * x_offset
                        if not is_helper(subgraph.nodes[node].get("label", node))
                        else None
                    ),
                    y=(
                        idx * y_spacing
                        if not is_helper(subgraph.nodes[node].get("label", node))
                        else None
                    ),
                    physics=False,
                    fixed=False,
                )

            # add edges between duplicates
            for src, dst, data in subgraph.edges(data=True):
                if src in topo_nodes and dst in topo_nodes:
                    edge_color = "rgba(128,128,128,0.5)" if is_gray else None
                    if is_gray:
                        net.add_edge(
                            dup_map_global[(src, root)],
                            dup_map_global[(dst, root)],
                            color=edge_color,
                            width=1,
                            physics=False,
                        )
        return dup_map_global

    # -------------------- WORKFLOW HIGHLIGHT --------------------
    def _highlight_workflows(self, net, subgraph, nodes, show_sequence=True):
        if not show_sequence:
            return

        def _big_color_palette(n_colors=120):
            colors = []
            golden_ratio_conjugate = 0.6180339887
            h = 0
            for i in range(n_colors):
                h = (h + golden_ratio_conjugate) % 1
                r, g, b = colorsys.hsv_to_rgb(h, 0.6, 0.95)
                colors.append(
                    "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))
                )
            return colors

        palette = _big_color_palette(120)
        color_iter = iter(palette)
        used_colors = set()

        def next_color():
            while True:
                color = next(color_iter)
                if color not in used_colors:
                    used_colors.add(color)
                    return color

        def is_helper(label: str) -> bool:
            return (
                label.startswith("__")
                or label.startswith("_external_")
                or label == "<external>"
            )

        entrypoints = [
            n
            for n in nodes
            if subgraph.in_degree(n) == 0
            and not is_helper(subgraph.nodes[n].get("label", n))
        ]

        x_offset = 300
        y_spacing = 160

        for w_idx, start in enumerate(entrypoints):
            reachable_nodes = nx.descendants(subgraph, start) | {start}
            reachable_nodes -= set(entrypoints) - {start}
            topo_nodes = list(nx.topological_sort(subgraph.subgraph(reachable_nodes)))
            flow_color = next_color()

            # workflow duplicates
            dup_ids = {}
            for idx, node in enumerate(topo_nodes):
                dup_id = f"{node}__wf{w_idx}"
                dup_ids[node] = dup_id
                net.add_node(
                    dup_id,
                    label=subgraph.nodes[node].get("label", node),
                    title=subgraph.nodes[node].get("label", node),
                    color=self.get_node_color(subgraph.nodes[node].get("label", node)),
                    x=(
                        w_idx * x_offset
                        if not is_helper(subgraph.nodes[node].get("label", node))
                        else None
                    ),
                    y=(
                        idx * y_spacing
                        if not is_helper(subgraph.nodes[node].get("label", node))
                        else None
                    ),
                    physics=False,
                    fixed=False,
                )

            workflow_nodes = [
                n
                for n in topo_nodes
                if not is_helper(subgraph.nodes[n].get("label", n))
            ]
            for i in range(len(workflow_nodes) - 1):
                net.add_edge(
                    dup_ids[workflow_nodes[i]],
                    dup_ids[workflow_nodes[i + 1]],
                    color=flow_color,
                    width=2,
                    physics=False,
                    smooth=False,
                    **{"workflow": True},
                )

    # -------------------- LEGEND --------------------
    def _add_legend(self, net, filename: Path):
        """
        Generate HTML with a fixed legend injected,
        then save to the given filename.
        """
        legend_html = """
        <div id="callchain-legend" style="
             position: fixed;
             right: 12px;
             top: 12px;
             z-index: 99999;
             background: rgba(255,255,255,0.95);
             border: 1px solid #cfcfcf;
             padding: 10px 12px;
             border-radius: 8px;
             box-shadow: 0 2px 8px rgba(0,0,0,0.08);
             font-family: Arial, Helvetica, sans-serif;
             font-size: 13px;
             color: #222;
             max-width: 240px;">
          <div style="font-weight:600; margin-bottom:6px;">Legend</div>
          <div style="line-height:1.5;">
            <div>🟩 File</div>
            <div>🟦 Top-level function / method</div>
            <div>🟥 Class</div>
            <div>🟪 Parameter</div>
            <div>💗 External call</div>
            <div>⚪ Other / unknown</div>
            <div>▫️ Structural / tree edges (gray)</div>
            <div>🌈 Workflow (bright colors)</div>
          </div>
        </div>
        """

        html = net.generate_html()
        if "</body>" in html:
            html = html.replace("</body>", legend_html + "\n</body>")
        else:
            html = html + legend_html

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

    # -------------------- MAIN --------------------
    def save_file_charts(
        self, folder="chains_output", prefix="chart", show_external=True
    ):
        timestamp_folder = Path(folder) / datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_folder.mkdir(parents=True, exist_ok=True)

        file_to_nodes = {}
        for node, data in self.graph.nodes(data=True):
            label = data.get("label", node)
            root_file = label.split("__")[0] if "__" in label else label
            file_to_nodes.setdefault(root_file, set()).add(node)

        for root_file, nodes in file_to_nodes.items():
            subgraph = self._build_subgraph(nodes, show_external)
            if subgraph is None:
                continue
            safe_file_root = self.sanitize_filename(root_file)
            net = self._create_network(hierarchical=True)

            # Add gray tree duplicates
            self._add_duplicate_tree(net, subgraph, is_gray=True)

            # Add workflow duplicates / edges
            self._highlight_workflows(net, subgraph, nodes, show_sequence=True)

            filename = timestamp_folder / f"{prefix}_{safe_file_root}.html"
            self._add_legend(net, filename)

            # -------------------- global chart --------------------
            global_subgraph = self.graph.copy()
            if not show_external:
                global_subgraph = global_subgraph.subgraph(
                    [
                        n
                        for n in global_subgraph.nodes
                        if not (
                            self.graph.nodes[n].get("label", n).startswith("_external_")
                            or self.graph.nodes[n].get("label", n) == "<external>"
                        )
                    ]
                ).copy()

            net = self._create_network(hierarchical=True)
            self._add_duplicate_tree(net, global_subgraph, is_gray=True)
            self._highlight_workflows(
                net, global_subgraph, list(global_subgraph.nodes), show_sequence=True
            )

            global_filename = timestamp_folder / f"{prefix}__GLOBAL.html"
            self._add_legend(net, global_filename)
