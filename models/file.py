from dataclasses import dataclass


@dataclass
class File:
    file_name: str
    file_format: str
    file_path: str
