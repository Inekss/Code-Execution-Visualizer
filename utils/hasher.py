import hashlib
from pathlib import Path
from typing import Dict

from models.file import File
from models.hash import FileHash


class FileHasher:
    """Utility to compute and store hashes for files."""

    def __init__(self):
        self.hashes: Dict[str, FileHash] = {}

    @staticmethod
    def compute_source_hash(source: str) -> str:
        """Compute SHA256 hash of source code string."""
        sha256 = hashlib.sha256()
        sha256.update(source.encode("utf-8"))
        return sha256.hexdigest()

    def add_file(self, file: File, source: str) -> FileHash:
        """Compute and store hash for a given file based on source string."""
        file_hash = self.compute_source_hash(source)
        fh = FileHash(file=file, hash=file_hash)
        self.hashes[file.file_path] = fh
        return fh

    def get_hash(self, file_path: str) -> str | None:
        """Retrieve previously stored hash."""
        return self.hashes[file_path].hash if file_path in self.hashes else None

    def diff(self, other: "FileHasher") -> Dict[str, str]:
        """Compare hashes with another run, return changed files."""
        changed = {}
        for path, file_hash in self.hashes.items():
            old_hash = other.hashes.get(path).hash if path in other.hashes else None
            if old_hash != file_hash.hash:
                changed[path] = file_hash.hash
        return changed

    def to_dict(self) -> Dict[str, dict]:
        """Convert stored FileHash objects to serializable dictionaries."""
        result = {}
        for path, file_hash in self.hashes.items():
            result[path] = {
                "file_name": file_hash.file.file_name,
                "file_format": file_hash.file.file_format,
                "file_path": file_hash.file.file_path,
                "hash": file_hash.hash,
            }
        return result
