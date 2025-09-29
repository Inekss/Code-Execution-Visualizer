import re
from typing import Optional

import networkx as nx


class ExecutionChainBuildProcessor:
    """Processor that builds execution chains from dependency roadmap."""

    def __init__(self, roadmap):
        self.roadmap = roadmap
        self.graph = nx.DiGraph()

    # -------------------- PUBLIC --------------------

    def build_graph(self):
        """Build a call graph including nested functions and classes."""
        if not self.roadmap or not getattr(self.roadmap, "map", None):
            return self.graph

        for dep in self.roadmap.map:
            self._add_registry_file(dep.registry)

            if getattr(dep, "calls", None) and getattr(dep.calls, "calls", None):
                for call in dep.calls.calls:
                    caller_name = self._format_caller(dep.calls, call)
                    callee_name = self._format_callee(call)

                    caller = self._add_node_with_label(caller_name)
                    callee = self._add_node_with_label(callee_name)

                    file_key = self._get_file_key_from_registry(dep.registry)
                    self.graph.add_edge(caller, callee, file=file_key)

        return self.graph

    def _get_file_key_from_registry(self, registry) -> str:
        """Return best available file identifier for a registry object."""
        fileobj = getattr(registry, "file", None)
        return self._get_file_key_from_file(fileobj)

    def _get_file_key_from_file(self, fileobj) -> str:
        """
        Try multiple attributes to build a unique file key.
        Fallbacks: file_path, path, relative_path, full_path, module_path, module, package, file_name, name.
        If nothing found — returns string(fileobj) or '<unknown>'.
        """
        if not fileobj:
            return "<unknown>"

        # attributes to check (ordered by preference)
        attrs = (
            "file_path",
            "path",
            "relative_path",
            "full_path",
            "module_path",
            "module",
            "package",
            "file_name",
            "name",
        )
        for a in attrs:
            val = getattr(fileobj, a, None)
            if val:
                return str(val)

        try:
            return str(fileobj)
        except Exception:
            return "<unknown>"

    # -------------------- ADD REGISTRY (classes/functions) --------------------

    def _add_registry_file(self, registry_file):
        """
        Add classes/functions defined in a registry file.
        We compute a 'file_key' once for the registry and pass it down.
        """
        file_key = self._get_file_key_from_file(getattr(registry_file, "file", None))

        # classes
        for cls in getattr(registry_file, "classes", []) or []:
            self._add_registry_class(cls, file_key)

        # top-level functions
        for func in getattr(registry_file, "functions", []) or []:
            self._add_registry_function(func, file_key)

    def _add_registry_class(self, cls, parent_file_key):
        """Add class node and its nested classes/functions."""
        cls_label = f"{parent_file_key}__{cls.class_name}"
        cls_node = self._add_node_with_label(cls_label)

        # nested classes
        for subcls in getattr(cls, "classes", []) or []:
            sub_node = self._add_registry_class(subcls, parent_file_key)
            self.graph.add_edge(cls_node, sub_node)

        # class functions
        for func in getattr(cls, "class_functions", []) or []:
            func_node = self._add_registry_function(func, parent_file_key)
            self.graph.add_edge(cls_node, func_node)

        return cls_node

    def _add_registry_function(self, func, parent_file_key):
        """Add function node and nested functions."""
        node_label = f"{parent_file_key}__{func.function_name}"
        func_node = self._add_node_with_label(node_label)

        # nested functions
        for subfunc in getattr(func, "functions", []) or []:
            sub_node = self._add_registry_function(subfunc, parent_file_key)
            self.graph.add_edge(func_node, sub_node)

        return func_node

    # -------------------- NODE / LABEL helpers --------------------

    def _add_node_with_label(self, label: str) -> str:
        """
        Ensure safe node id (no special chars) and add node with readable 'label' attribute.
        Returns the node id used in the graph.
        """
        # make a safe id (replace anything non-alnum/underscore/dot by underscore)
        safe_id = re.sub(r"[^0-9A-Za-z_.\-]", "_", label)

        if safe_id in self.graph.nodes:
            existing_label = self.graph.nodes[safe_id].get("label")
            if existing_label == label:
                return safe_id
            i = 1
            new_id = f"{safe_id}_{i}"
            while new_id in self.graph.nodes:
                i += 1
                new_id = f"{safe_id}_{i}"
            safe_id = new_id

        self.graph.add_node(safe_id, label=label)
        return safe_id

    # -------------------- FORMAT CALLER / CALLEE --------------------

    def _format_callee(self, call) -> str:
        parts = []
        if getattr(call, "called_file", None):
            parts.append(self._get_file_key_from_file(call.called_file))
        else:
            parts.append("<external>")
        if getattr(call, "parent_class", None):
            parts.append(call.parent_class)
        if getattr(call, "called_func", None):
            parts.append(call.called_func)
        return "__".join(parts)

    def _format_caller(self, calls, call) -> str:
        parts = []
        if getattr(calls, "caller_file", None):
            parts.append(self._get_file_key_from_file(calls.caller_file))
        else:
            parts.append("<unknown>")
        if getattr(call, "caller_class", None):
            parts.append(call.caller_class)
        if getattr(call, "caller_func", None):
            parts.append(call.caller_func)
        return "__".join(parts)

    # -------------------- EXTRACT ENTRYPOINTS --------------------

    def extract_entrypoint_chains(self, cutoff: int = 20):
        """Extract one execution tree per root node including all nested elements."""
        chains = []
        entrypoints = [n for n in self.graph.nodes if self.graph.in_degree(n) == 0]
        for entry in entrypoints:
            tree = nx.dfs_tree(self.graph, source=entry, depth_limit=cutoff)
            chains.append(list(tree.nodes))
        return chains
