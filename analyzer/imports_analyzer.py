import ast

from models.file import File
from models.imports import Import, Imports


class ImportsAnalyzer:
    """Analyzes imports in a file from a given AST."""

    @staticmethod
    def analyze_file_ast(file_ast: ast.Module, file_meta: File) -> Imports:
        """Return Imports for a single file."""
        imports: Imports.imports = []
        for node in ast.walk(file_ast):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        Import(
                            imported_name=alias.asname or alias.name,
                            imported_from=alias.name.replace(".", "/") + ".py",
                        )
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    imports.append(
                        Import(
                            imported_name=alias.asname or alias.name,
                            imported_from=node.module.replace(".", "/") + ".py",
                        )
                    )
        return Imports(file=file_meta, imports=imports)
