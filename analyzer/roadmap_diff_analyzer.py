from typing import Dict, List

from models.versions import FileChange, FunctionChange


class RoadmapDiff:
    """Responsible for extracting and comparing functions/classes per file."""

    def __init__(self, roadmap: dict):
        self.roadmap = roadmap
        self.funcs_by_file = self._functions_by_file(roadmap)

    def _functions_by_file(self, roadmap: dict) -> Dict[str, List[dict]]:
        """Collect all functions per file recursively."""
        funcs_by_file = {}

        def collect_funcs(func_list, parent_class=None, parent_function=None):
            res = []
            for f in func_list:
                func_dict = {
                    "function_name": f["function_name"],
                    "parameters": f.get("parameters", []),
                    "param_types": f.get("param_types", []),
                    "parent_class": parent_class,
                    "parent_function": parent_function,
                }
                res.append(func_dict)
                if f.get("functions"):
                    res.extend(
                        collect_funcs(
                            f["functions"],
                            parent_class=parent_class,
                            parent_function=f["function_name"],
                        )
                    )
            return res

        for entry in roadmap.get("map", []):
            file_path = entry["registry"]["file"]["file_path"]
            funcs_by_file[file_path] = collect_funcs(
                entry["registry"].get("functions", [])
            )

        return funcs_by_file

    def diff(self, other: "RoadmapDiff") -> List[FileChange]:
        """Compare self to another roadmap and return structured file changes."""
        files_changes = []
        all_files = set(self.funcs_by_file.keys()) | set(other.funcs_by_file.keys())

        for file in all_files:
            added_funcs = [
                FunctionChange(**f)
                for f in other.funcs_by_file.get(file, [])
                if f not in self.funcs_by_file.get(file, [])
            ]
            removed_funcs = [
                FunctionChange(**f)
                for f in self.funcs_by_file.get(file, [])
                if f not in other.funcs_by_file.get(file, [])
            ]
            if added_funcs or removed_funcs:
                files_changes.append(
                    FileChange(
                        file_path=file,
                        added_functions=added_funcs,
                        removed_functions=removed_funcs,
                        added_classes=[],
                        removed_classes=[],
                    )
                )
        return files_changes
