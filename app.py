from pathlib import Path

from processors.processor import Processor
from utils.console import Console
from utils.writer import Writer


class App:
    """Main entry point of the application."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def run(self):
        processor = Processor(self.base_path)
        roadmap = processor.run()
        Console().print(roadmap)
        Writer.save_dependency_roadmap_json(roadmap)


if __name__ == "__main__":
    app = App(base_path="resources/test_data")
    app.run()
