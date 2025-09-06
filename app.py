import time
from pathlib import Path

from processors.processor import Processor
from utils.console import Console
from utils.writer import Writer


class App:
    """Main entry point of the application."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def run(self):
        start = time.perf_counter()

        processor = Processor(self.base_path)
        roadmap, hash_map = processor.run()

        Writer.save_dependency_roadmap_json(roadmap)

        end = time.perf_counter()
        elapsed = end - start

        Console().print(roadmap)
        Console().print(
            f"[green]Seed processing completed successfully in {elapsed:.4f} seconds[/green]"
        )


if __name__ == "__main__":
    app = App(base_path="resources/test_data")
    app.run()
