from pathlib import Path
from typing import List

from analyzer.imports_analyzer import ImportsAnalyzer
from analyzer.register import Register
from models.dependencies import Dependency, DependencyRoadMap
from models.file import File
from utils.reader import Reader


class Processor:
    """Processes a project folder to extract registry and imports per file."""

    def __init__(self, base_path: Path):
        self.base_path = base_path

    def run(self) -> DependencyRoadMap:
        roadmap: DependencyRoadMap.map = []

        # Iterate over all Python files
        for py_file in self.base_path.rglob("*.py"):
            # Read the AST once
            file_ast = Reader.parse_file(py_file)
            file_meta = File(
                file_name=py_file.name,
                file_format=py_file.suffix,
                file_path=str(py_file.relative_to(self.base_path)),
            )

            # Build registry for this file
            registry_file = Register.build_registry(file_ast, file_meta)

            # Analyze imports for this file
            file_imports = ImportsAnalyzer.analyze_file_ast(file_ast, file_meta)

            # Add to roadmap
            roadmap.append(Dependency(registry=registry_file, imports=file_imports))

        return DependencyRoadMap(map=roadmap)
