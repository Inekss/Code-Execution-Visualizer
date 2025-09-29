from pathlib import Path

from processors.execution_chain_build_processor import ExecutionChainBuildProcessor
from processors.processor import Processor
from processors.version_diff_processor import VersionProcessor
from utils.console import Console
from utils.visualizer import CallChainVisualizer
from utils.writer import Writer


class App:
    """Main entry point of the application."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def run(self):
        processor = Processor(self.base_path)
        roadmap, hash_map = processor.run()

        Writer.save_dependency_roadmap_json(roadmap)
        Writer.save_file_hashes_json(hash_map)

        data_dir = Path(__file__).parent / "data"
        version_processor = VersionProcessor(data_dir)
        try:
            report = version_processor.compare_latest_versions()
            Console().print(report)
        except FileNotFoundError:
            Console().print(
                "[yellow]No previous roadmap found, skipping version comparison[/yellow]"
            )

        chain_processor = ExecutionChainBuildProcessor(roadmap)
        graph = chain_processor.build_graph()

        visualizer = CallChainVisualizer(graph)
        visualizer.save_file_charts(prefix="", folder="chains_output")


if __name__ == "__main__":
    app = App(base_path="resources/test_data")
    app.run()
