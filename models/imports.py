from dataclasses import dataclass
from typing import List, Optional

from models.file import File


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
