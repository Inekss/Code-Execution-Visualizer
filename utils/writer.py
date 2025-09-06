import json
from dataclasses import is_dataclass
from pathlib import Path
from typing import Dict

from models.file import File


class Writer:
    """Responsible for saving dependency roadmap to JSON."""

    @staticmethod
    def save_dependency_roadmap_json(
        roadmap, file_name: str = "dependency_roadmap.json"
    ):
        project_root = Path(__file__).parent.parent
        data_dir = project_root / "data"
        data_dir.mkdir(exist_ok=True)
        file_path = data_dir / file_name

        data = Writer.dataclass_to_dict(roadmap)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        print(f"Dependency roadmap saved to {file_path}")

    @staticmethod
    def save_file_hashes_json(
        hashes: Dict[str, dict], file_name: str = "file_hashes.json"
    ) -> None:
        project_root = Path(__file__).parent.parent
        data_dir = project_root / "data"
        data_dir.mkdir(exist_ok=True)
        file_path = data_dir / file_name

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(hashes, f, indent=4)

        print(f"File hashes saved to {file_path}")

    @staticmethod
    def dataclass_to_dict(obj, seen=None):
        """
        Recursively convert dataclass to dict while avoiding circular references.
        Ensures param_types exists with None values if missing.
        """
        global parameters
        if seen is None:
            seen = set()

        if isinstance(obj, File):
            return {
                "file_name": obj.file_name,
                "file_format": obj.file_format,
                "file_path": obj.file_path,
            }

        if id(obj) in seen:
            return None
        seen.add(id(obj))

        if is_dataclass(obj):
            result = {}
            for k, v in obj.__dict__.items():
                if k == "parent_file":
                    result[k] = getattr(getattr(v, "file", None), "file_name", None)
                elif k == "parent_class":
                    result[k] = getattr(v, "class_name", None)
                elif k == "parent_function":
                    result[k] = getattr(v, "function_name", None)
                elif v is None:
                    result[k] = None
                elif isinstance(v, list):
                    result[k] = [Writer.dataclass_to_dict(i, seen) for i in v]
                elif is_dataclass(v):
                    result[k] = Writer.dataclass_to_dict(v, seen)
                else:
                    result[k] = v

            if hasattr(obj, "parameters"):
                parameters = getattr(obj, "parameters") or []
                result["parameters"] = parameters

            if hasattr(obj, "param_types"):
                param_types = getattr(obj, "param_types")
                if param_types is None:
                    param_types = [None] * len(parameters)
                result["param_types"] = param_types

            if hasattr(obj, "arguments"):
                result["arguments"] = getattr(obj, "arguments", None)

            return result

        return obj
