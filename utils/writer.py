import json
from pathlib import Path

from models.registry import Registry


class Writer:
    """Responsible for saving registry data to file."""

    @staticmethod
    def save_registry_json(registry: Registry, file_name: str = "registry.json"):
        """
        Save the Registry object as a JSON file in the /data directory
        at the project root.
        """
        project_root = Path(__file__).parent.parent  # go up from /utils to project root
        data_dir = project_root / "data"
        data_dir.mkdir(exist_ok=True)  # create /data if it doesn't exist

        file_path = data_dir / file_name

        def dataclass_to_dict(obj):
            if hasattr(obj, "__dataclass_fields__"):
                result = {}
                for k, v in obj.__dict__.items():
                    if k == "parent_file":
                        result[k] = v.file_name if v else None
                    elif k == "parent_class":
                        result[k] = v.class_name if v else None
                    elif k == "parent_function":
                        result[k] = v.function_name if v else None
                    elif isinstance(v, list):
                        result[k] = [dataclass_to_dict(i) for i in v]
                    else:
                        result[k] = v
                return result
            return obj

        data = dataclass_to_dict(registry)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        print(f"Registry saved to {file_path}")
