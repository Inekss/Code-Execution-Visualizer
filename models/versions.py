from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class FunctionChange:
    function_name: str
    parameters: List[str]
    param_types: List[Optional[str]]
    parent_class: Optional[str] = None
    parent_function: Optional[str] = None


@dataclass
class ClassChange:
    class_name: str
    nested_classes: List["ClassChange"]
    class_functions: List[FunctionChange]
    parent_class: Optional[str] = None
    parent_file: Optional[str] = None
    parent_function: Optional[str] = None


@dataclass
class FileChange:
    file_path: str
    added_functions: List[FunctionChange]
    removed_functions: List[FunctionChange]
    added_classes: List[ClassChange]
    removed_classes: List[ClassChange]


@dataclass
class StructuredRoadmapChanges:
    files: List[FileChange]


@dataclass
class VersionReport:
    old_version: str
    new_version: str
    hash_changes: Dict[str, Any]
    roadmap_changes: StructuredRoadmapChanges
