from dataclasses import dataclass
from typing import List, Optional

from models.file import File


@dataclass
class Call:
    caller_file: File
    caller_class: str
    caller_func: str
    called_file: File
    called_class: str
    called_func: str


@dataclass
class Calls:
    calls: Optional[List[Call]]


@dataclass
class Import:
    imported_name: str
    imported_from: str


@dataclass
class Imports:
    file: File
    imports: Optional[List[Import]]


@dataclass
class ImportsHeap:
    imports: Optional[List[Imports]]
