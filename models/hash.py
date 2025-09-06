from dataclasses import dataclass
from typing import Dict

from models.file import File


@dataclass
class ASTCache:
    """Cache parsed ASTs to avoid reparsing files."""

    cache: Dict[str, object]


@dataclass
class SymbolIndex:
    """Global index of symbols (functions/classes) for fast lookup."""

    index: Dict[str, File]


@dataclass
class FileHash:
    """File hash to detect changes between runs."""

    file: File
    hash: str


@dataclass
class FileHashCache:
    """Store hashes for all files in a run."""

    hashes: Dict[str, FileHash]
