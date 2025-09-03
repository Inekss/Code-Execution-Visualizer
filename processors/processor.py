from pathlib import Path

from analyzer.register import Register
from models.registry import Registry


class Processor:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.registry: Registry | None = None

    def run(self):
        self.registry = Register.build_registry(self.base_path)
        return self.registry
