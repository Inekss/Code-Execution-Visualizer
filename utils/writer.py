import json
from dataclasses import is_dataclass
from pathlib import Path

from models.dependencies import DependencyRoadMap


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
    def dataclass_to_dict(obj):
        if is_dataclass(obj):
            result = {}
            for k, v in obj.__dict__.items():
                # Break recursion for parent references
                if k == "parent_file":
                    result[k] = (
                        getattr(v.file, "file_name", None)
                        if v and hasattr(v, "file")
                        else None
                    )
                elif k == "parent_class":
                    result[k] = getattr(v, "class_name", None) if v else None
                elif k == "parent_function":
                    result[k] = getattr(v, "function_name", None) if v else None
                elif v is None:
                    result[k] = None
                elif isinstance(v, list):
                    result[k] = [Writer.dataclass_to_dict(i) for i in v]
                elif is_dataclass(v):
                    result[k] = Writer.dataclass_to_dict(v)
                else:
                    result[k] = v
            return result
        return obj
