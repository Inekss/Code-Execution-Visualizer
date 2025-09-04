from pathlib import Path
from typing import List

from analyzer.call_analyzer import CallAnalyzer
from analyzer.imports_analyzer import ImportsAnalyzer
from analyzer.register import Register
from models.dependencies import Dependency, DependencyRoadMap
from models.file import File
from models.imports import ImportsHeap
from models.registry import RegistryHeap
from utils.reader import Reader


class Processor:
    """Processes a project folder to extract registry, imports, and calls per file."""

    def __init__(self, base_path: Path):
        self.base_path = base_path

    def run(self) -> DependencyRoadMap:
        registry_heap = RegistryHeap(files=[])
        imports_heap = ImportsHeap(imports=[])

        # --- First pass: build registry and imports heaps ---
        for py_file in self.base_path.rglob("*.py"):
            file_ast = Reader.parse_file(py_file)
            file_meta = File(
                file_name=py_file.name,
                file_format=py_file.suffix,
                file_path=str(py_file.relative_to(self.base_path)),
            )

            registry_file = Register.build_registry(file_ast, file_meta)
            registry_heap.files.append(registry_file)

            file_imports = ImportsAnalyzer.analyze_file_ast(file_ast, file_meta)
            imports_heap.imports.append(file_imports)

        # --- Second pass: analyze calls using the full registry heap ---
        roadmap: List[Dependency] = []

        for registry_file in registry_heap.files:
            # Load AST again for this file
            py_file_path = self.base_path / registry_file.file.file_path
            file_ast = Reader.parse_file(py_file_path)
            file_meta = registry_file.file

            file_calls = CallAnalyzer.analyze_file_ast(
                file_ast, file_meta, registry_heap
            )

            # Find corresponding imports
            file_imports = next(
                (
                    imp
                    for imp in imports_heap.imports
                    if imp.file.file_name == file_meta.file_name
                ),
                None,
            )

            roadmap.append(
                Dependency(
                    registry=registry_file, imports=file_imports, calls=file_calls
                )
            )

        return DependencyRoadMap(map=roadmap)
