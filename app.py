import json
import time
from pathlib import Path

from processors.processor import Processor
from processors.version_diff_processor import VersionDiffProcessor
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
        Writer.save_file_hashes_json(hash_map)

        end = time.perf_counter()
        elapsed = end - start

        # Console().print(roadmap)
        Console().print(
            f"[green]Seed processing completed successfully in {elapsed:.4f} seconds[/green]"
        )

        project_root = Path(__file__).parent  # not .parent.parent
        data_dir = project_root / "data"

        diff_proc = VersionDiffProcessor(data_dir)
        report = diff_proc.compare_latest()
        Console().print(report)


if __name__ == "__main__":
    app = App(base_path="resources/test_data")
    app.run()
