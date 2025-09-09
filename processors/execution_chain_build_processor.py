import networkx as nx

from models.calls import Call, Calls
from models.dependencies import DependencyRoadMap


class ExecutionChainBuildProcessor:
    """Processor that builds execution chains from dependency roadmap."""

    def __init__(self, roadmap: DependencyRoadMap):
        self.roadmap = roadmap
        self.graph = nx.DiGraph()

    def build_graph(self):
        """Build a call graph including nested functions and classes."""
        if not self.roadmap or not self.roadmap.map:
            return self.graph

        for dep in self.roadmap.map:

            # Add all classes and functions recursively
            self._add_registry_file(dep.registry)

            # Add call edges
            if dep.calls and dep.calls.calls:
                for call in dep.calls.calls:
                    caller_name = self._format_caller(dep.calls, call)
                    callee_name = self._format_callee(call)

                    caller = self._add_node_with_label(caller_name)
                    callee = self._add_node_with_label(callee_name)

                    self.graph.add_edge(
                        caller, callee, file=dep.registry.file.file_name
                    )

        return self.graph

    def _add_registry_file(self, registry_file):
        # Add all classes
        for cls in registry_file.classes:
            self._add_registry_class(cls, registry_file.file.file_name)

        # Add all functions
        for func in registry_file.functions:
            self._add_registry_function(func, registry_file.file.file_name)

    def _add_registry_class(self, cls, parent_file):
        cls_node = self._add_node_with_label(f"{parent_file}__{cls.class_name}")

        # Add nested classes
        for subcls in cls.classes:
            sub_node = self._add_registry_class(subcls, parent_file)
            self.graph.add_edge(cls_node, sub_node)

        # Add class functions
        for func in cls.class_functions:
            func_node = self._add_registry_function(func, parent_file)
            self.graph.add_edge(cls_node, func_node)

        return cls_node

    def _add_registry_function(self, func, parent_file):
        node_label = f"{parent_file}__{func.function_name}"
        func_node = self._add_node_with_label(node_label)

        # Add nested functions
        for subfunc in func.functions:
            sub_node = self._add_registry_function(subfunc, parent_file)
            self.graph.add_edge(func_node, sub_node)

        return func_node

    def _add_node_with_label(self, label: str) -> str:
        """Ensure safe node id for Graphviz / PyVis."""
        safe_id = label.replace(":", "_").replace("<", "_").replace(">", "_")
        self.graph.add_node(safe_id, label=label)
        return safe_id

    def _format_callee(self, call: Call) -> str:
        parts = []
        if call.called_file:
            parts.append(call.called_file.file_name)
        else:
            parts.append("<external>")
        if call.parent_class:
            parts.append(call.parent_class)
        if call.called_func:
            parts.append(call.called_func)
        return "__".join(parts)

    def _format_caller(self, calls: Calls, call: Call) -> str:
        parts = []
        if calls.caller_file:
            parts.append(calls.caller_file.file_name)
        else:
            parts.append("<unknown>")
        if call.caller_class:
            parts.append(call.caller_class)
        if call.caller_func:
            parts.append(call.caller_func)
        return "__".join(parts)

    def extract_entrypoint_chains(self, cutoff: int = 20):
        """Extract one execution tree per root node including all nested elements."""
        chains = []

        # Entrypoints = nodes with no predecessors
        entrypoints = [n for n in self.graph.nodes if self.graph.in_degree(n) == 0]

        for entry in entrypoints:
            tree = nx.dfs_tree(self.graph, source=entry, depth_limit=cutoff)
            chains.append(list(tree.nodes))

        return chains
