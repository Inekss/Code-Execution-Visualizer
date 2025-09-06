from dataclasses import dataclass
from typing import Any, List, Optional

from models.file import File


@dataclass
class CallCoordinates:
    line: int
    char: int


@dataclass
class Call:
    called_file: File
    caller_class: Optional[str] = None
    caller_func: Optional[str] = None
    parent_class: Optional[str] = None
    called_func: Optional[str] = None
    coordinates: Optional[CallCoordinates] = None
    parameters: Optional[List[str]] = None
    param_types: Optional[List[str]] = None
    arguments: Optional[List[Any]] = None


@dataclass
class Calls:
    caller_file: File
    calls: Optional[List[Call]]


@dataclass
class CallsHeap:
    calls: Optional[List[Calls]]
