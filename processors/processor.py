from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple

from analyzer.call_analyzer import CallAnalyzer
from analyzer.imports_analyzer import ImportsAnalyzer
from analyzer.register import Register
from models.calls import Calls, CallsHeap
from models.dependencies import Dependency, DependencyRoadMap
from models.file import File
from models.imports import Imports, ImportsHeap
from models.registry import RegistryClass, RegistryFile, RegistryHeap
from utils.hasher import FileHasher
from utils.reader import Reader


class Processor:
    def __init__(self, base_path: Path):
        self.base_path: Path = base_path
        self.file_hasher: FileHasher = FileHasher()

    def run(self) -> Tuple[DependencyRoadMap, dict[str, dict]]:
        registry_heap: RegistryHeap = RegistryHeap(files=[])
        imports_heap: ImportsHeap = ImportsHeap(imports=[])
        calls_heap: CallsHeap = CallsHeap(calls=[])

        py_files = list(self.base_path.rglob("*.py"))
        with ProcessPoolExecutor() as executor:
            futures = {
                executor.submit(
                    self._process_single_file, py_file, self.base_path
                ): py_file
                for py_file in py_files
            }

            for future in as_completed(futures):
                file_meta, reg_file, imp_file, calls_file, source = future.result()
                self.file_hasher.add_file(file_meta, source)
                registry_heap.files.append(reg_file)
                imports_heap.imports.append(imp_file)
                calls_heap.calls.append(calls_file)

        # Build func/class -> file map
        func_to_file_map: Dict[str, File] = {}
        for reg_file in registry_heap.files:
            for f in reg_file.functions:
                func_to_file_map[f.function_name] = reg_file.file

            def walk_class(cls: RegistryClass):
                func_to_file_map[cls.class_name] = reg_file.file
                for f in cls.class_functions:
                    func_to_file_map[f.function_name] = reg_file.file
                for sub_cls in cls.classes:
                    walk_class(sub_cls)

            for cls in reg_file.classes:
                walk_class(cls)

        # Fill called_file for calls
        for calls in calls_heap.calls:
            for call in calls.calls or []:
                if call.called_func and not call.called_file:
                    call.called_file = func_to_file_map.get(call.called_func)

        # Build dependency roadmap
        imports_dict = {i.file.file_path: i for i in imports_heap.imports}
        calls_dict = {c.caller_file.file_path: c for c in calls_heap.calls}

        roadmap: List[Dependency] = []
        for reg_file in registry_heap.files:
            file_path = reg_file.file.file_path
            dep = Dependency(
                registry=reg_file,
                imports=imports_dict.get(file_path),
                calls=calls_dict.get(file_path),
            )
            roadmap.append(dep)

        dependency_map = DependencyRoadMap(map=roadmap)
        return dependency_map, self.file_hasher.to_dict()

    @staticmethod
    def _process_single_file(
        py_file: Path, base_path: Path
    ) -> Tuple[File, RegistryFile, Imports, Calls, str]:
        source: str = py_file.read_text(encoding="utf-8")
        file_ast = Reader.parse_source(source)

        file_meta = File(
            file_name=py_file.name,
            file_format=py_file.suffix,
            file_path=str(py_file.relative_to(base_path)),
        )

        reg_file = Register.build_registry(file_ast, file_meta)
        imp_file = ImportsAnalyzer.analyze_file_ast(file_ast, file_meta)

        imports_map = {
            imp.imported_name: imp.imported_from for imp in imp_file.imports or []
        }

        calls_file = CallAnalyzer.analyze_file_ast(
            file_ast, file_meta, RegistryHeap(files=[]), imports_map
        )

        return file_meta, reg_file, imp_file, calls_file, source
