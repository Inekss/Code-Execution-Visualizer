from dataclasses import dataclass
from typing import List, Optional

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


@dataclass
class Calls:
    caller_file: File
    calls: Optional[List[Call]]


@dataclass
class CallsHeap:
    calls: Optional[List[Calls]]
