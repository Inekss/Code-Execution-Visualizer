from pathlib import Path
from typing import Optional

from analyzer.roadmap_diff_analyzer import RoadmapDiff
from models.versions import (
    FileChange,
    FunctionChange,
    StructuredRoadmapChanges,
    VersionReport,
)
from utils.reader import Reader


class VersionProcessor:
    """Handles loading versions and comparing them."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def compare_latest_versions(self) -> Optional[VersionReport]:
        """Load latest two versions and return a VersionReport."""
        dirs = sorted(
            [d for d in self.data_dir.iterdir() if d.is_dir()], key=lambda d: d.name
        )
        if len(dirs) < 2:
            return None  # Not enough versions

        old_dir, new_dir = dirs[-2], dirs[-1]

        old_roadmap = Reader.read_json(old_dir / "dependency_roadmap.json")
        new_roadmap = Reader.read_json(new_dir / "dependency_roadmap.json")
        old_hashes = Reader.read_json(old_dir / "file_hashes.json")
        new_hashes = Reader.read_json(new_dir / "file_hashes.json")

        # Compute hash changes
        hash_changes = {}
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

        # Only compute roadmap diffs for files that changed
        files_changes = []
        if hash_changes:
            old_diff = RoadmapDiff(old_roadmap)
            new_diff = RoadmapDiff(new_roadmap)

            # Filter diff by files that have hash changes
            changed_files = set(hash_changes.keys())
            for file in changed_files:
                added_funcs = [
                    FunctionChange(**f)
                    for f in new_diff.funcs_by_file.get(file, [])
                    if f not in old_diff.funcs_by_file.get(file, [])
                ]
                removed_funcs = [
                    FunctionChange(**f)
                    for f in old_diff.funcs_by_file.get(file, [])
                    if f not in new_diff.funcs_by_file.get(file, [])
                ]

                if added_funcs or removed_funcs:
                    files_changes.append(
                        FileChange(
                            file_path=file,
                            added_functions=added_funcs,
                            removed_functions=removed_funcs,
                            added_classes=[],  # can extend later
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
