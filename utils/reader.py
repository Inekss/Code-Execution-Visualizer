import ast
from pathlib import Path


class Reader:
    """Responsible for reading Python files and returning their AST."""

    @staticmethod
    def parse_file(file_path: Path) -> ast.Module:
        with open(file_path, "r", encoding="utf-8") as f:
            return ast.parse(f.read(), filename=str(file_path))

    @staticmethod
    def parse_source(source: str) -> ast.Module:
        """Parse a source string directly into an AST."""
        return ast.parse(source)
