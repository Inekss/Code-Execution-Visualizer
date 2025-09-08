from pathlib import Path
from typing import Any, Dict, List, Optional

from models.versions import (
    FileChange,
    FunctionChange,
    StructuredRoadmapChanges,
    VersionReport,
)
from utils.reader import Reader


class VersionDiffProcessor:

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)

    def _get_latest_versions(self) -> Optional[tuple[Path, Path]]:
        dirs = [d for d in self.base_dir.iterdir() if d.is_dir()]
        if len(dirs) < 2:
            return None  # Not enough versions to compare

        dirs_sorted = sorted(dirs, key=lambda d: d.name)
        return dirs_sorted[-2], dirs_sorted[-1]

    def load_version(self, version_dir: Path) -> tuple[Dict[str, Any], Dict[str, Any]]:
        roadmap_file = version_dir / "dependency_roadmap.json"
        hashes_file = version_dir / "file_hashes.json"

        roadmap = Reader.read_json(roadmap_file)
        hashes = Reader.read_json(hashes_file)

        return roadmap, hashes

    def compare_latest(self) -> VersionReport:
        versions = self._get_latest_versions()
        if not versions:
            return VersionReport(
                old_version="",
                new_version="",
                hash_changes={},
                roadmap_changes=StructuredRoadmapChanges(files=[]),
            )

        old_dir, new_dir = versions
        old_roadmap, old_hashes = self.load_version(old_dir)
        new_roadmap, new_hashes = self.load_version(new_dir)

        hash_changes = {}
        # 1) Compare file hashes
        for file_path, old_data in old_hashes.items():
            new_data = new_hashes.get(file_path)
            if not new_data:
                hash_changes[file_path] = {"status": "removed"}
            elif old_data["hash"] != new_data["hash"]:
                hash_changes[file_path] = {
                    "status": "modified",
                    "old_hash": old_data["hash"],
                    "new_hash": new_data["hash"],
                }
        for file_path in new_hashes.keys() - old_hashes.keys():
            hash_changes[file_path] = {"status": "added"}

        # 2) Compare roadmap if hash changes exist
        files_changes = []
        if hash_changes:
            old_funcs_by_file = self._functions_by_file(old_roadmap)
            new_funcs_by_file = self._functions_by_file(new_roadmap)

            all_files = set(old_funcs_by_file.keys()) | set(new_funcs_by_file.keys())

            for file in all_files:
                added_funcs = [
                    FunctionChange(**f)
                    for f in new_funcs_by_file.get(file, [])
                    if f not in old_funcs_by_file.get(file, [])
                ]
                removed_funcs = [
                    FunctionChange(**f)
                    for f in old_funcs_by_file.get(file, [])
                    if f not in new_funcs_by_file.get(file, [])
                ]

                if not added_funcs and not removed_funcs:
                    continue

                files_changes.append(
                    FileChange(
                        file_path=file,
                        added_functions=added_funcs,
                        removed_functions=removed_funcs,
                        added_classes=[],  # Extend for classes similarly
                        removed_classes=[],
                    )
                )

        roadmap_changes = StructuredRoadmapChanges(files=files_changes)
        return VersionReport(
            old_version=old_dir.name,
            new_version=new_dir.name,
            hash_changes=hash_changes,
            roadmap_changes=roadmap_changes,
        )

    def _functions_by_file(self, roadmap: dict) -> Dict[str, List[dict]]:
        """
        Helper: collect all functions per file from roadmap recursively.
        Returns a dict: {file_path: [func_dicts]}
        """
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

    def _extract_functions(self, roadmap: dict) -> set[str]:
        """Helper: pull all function names from roadmap map, recursively."""
        funcs = set()

        def collect(func_list):
            for f in func_list:
                funcs.add(f["function_name"])
                if f.get("functions"):
                    collect(f["functions"])

        for entry in roadmap.get("map", []):
            collect(entry["registry"].get("functions", []))

        return funcs
