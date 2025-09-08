import ast
import json
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

    @staticmethod
    def read_json(file_path: Path) -> dict:
        """Load a JSON file into a Python dict."""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
