from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RegistryFunction:
    function_name: str
    sub_function_of: Optional[str] = None
    parent_class: Optional[RegistryClass] = None
    parent_file: Optional[RegistryFile] = None
    parent_function: Optional[RegistryFunction] = None
    functions: List[RegistryFunction] = field(default_factory=list)

    def __repr__(self):
        return (
            f"RegistryFunction(function_name='{self.function_name}', "
            f"parent_class='{self.parent_class.class_name if self.parent_class else None}', "
            f"parent_file='{self.parent_file.file_name if self.parent_file else None}', "
            f"parent_function='{self.parent_function.function_name if self.parent_function else None}', "
            f"functions={self.functions})"
        )


@dataclass
class RegistryClass:
    class_name: str
    sub_class_of: Optional[str] = None
    parent_file: Optional[RegistryFile] = None
    parent_class: Optional[RegistryClass] = None
    parent_function: Optional[RegistryFunction] = None
    classes: List[RegistryClass] = field(default_factory=list)
    class_functions: List[RegistryFunction] = field(default_factory=list)

    def __repr__(self):
        return (
            f"RegistryClass(class_name='{self.class_name}', "
            f"parent_class='{self.parent_class.class_name if self.parent_class else None}', "
            f"parent_file='{self.parent_file.file_name if self.parent_file else None}', "
            f"parent_function='{self.parent_function.function_name if self.parent_function else None}', "
            f"classes={self.classes}, class_functions={self.class_functions})"
        )


@dataclass
class RegistryFile:
    file_name: str
    file_format: str
    file_path: str
    classes: List[RegistryClass] = field(default_factory=list)
    functions: List[RegistryFunction] = field(default_factory=list)

    def __repr__(self):
        return (
            f"RegistryFile(file_name='{self.file_name}', "
            f"classes={self.classes}, functions={self.functions})"
        )


@dataclass
class Registry:
    files: List[RegistryFile] = field(default_factory=list)

    def __repr__(self):
        return f"Registry(files={self.files})"
