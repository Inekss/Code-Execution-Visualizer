from dataclasses import dataclass
from typing import List, Optional

from models.calls import Calls
from models.imports import Imports, ImportsHeap
from models.registry import RegistryFile, RegistryHeap


@dataclass
class Dependency:
    registry: RegistryFile
    imports: Imports
    calls: Calls


@dataclass
class DependencyRoadMap:
    map: Optional[List[Dependency]]


@dataclass
class DependencyHeap:
    registry_heap: RegistryHeap
    imports_heap: ImportsHeap
