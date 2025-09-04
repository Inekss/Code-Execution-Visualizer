import ast
from typing import List, Optional

from models.calls import Call, CallCoordinates, Calls
from models.file import File
from models.registry import RegistryHeap


class CallAnalyzer:
    """Analyzes function calls in a file AST and returns structured Calls with coordinates, including OOP mapping."""

    @staticmethod
    def analyze_file_ast(
        file_ast: ast.Module, file_meta: File, registry_heap: RegistryHeap
    ) -> Calls:
        calls_list: List[Call] = []
        instance_map: dict[str, str] = {}  # var_name -> class_name

        # Helper: find class/method in registry
        def find_class_and_method(name: str) -> tuple[Optional[str], Optional[File]]:
            for reg_file in registry_heap.files:
                # Top-level functions
                for func in reg_file.functions:
                    if func.function_name == name:
                        return None, reg_file.file
                # Classes and methods
                for cls in reg_file.classes:
                    if cls.class_name == name:
                        return cls.class_name, reg_file.file
                    for func in cls.class_functions:
                        if func.function_name == name:
                            return cls.class_name, reg_file.file
            return None, None

        def visit(
            node: ast.AST, current_class: Optional[str], current_func: Optional[str]
        ):
            # Track class/function scope
            if isinstance(node, ast.ClassDef):
                current_class = node.name
            elif isinstance(node, ast.FunctionDef):
                current_func = node.name

            # Track instance assignments
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name):
                    class_name = node.value.func.id
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            instance_map[target.id] = class_name

            # Process function calls
            if isinstance(node, ast.Call):
                callee_name = None
                parent_class = None

                if isinstance(node.func, ast.Name):
                    callee_name = node.func.id
                    # Check if it's a top-level function or a method
                    parent_class, _ = find_class_and_method(callee_name)

                elif isinstance(node.func, ast.Attribute):
                    callee_name = node.func.attr
                    # Resolve the object/class
                    if isinstance(node.func.value, ast.Name):
                        obj_name = node.func.value.id
                        parent_class = instance_map.get(obj_name)
                        # fallback to registry
                        if parent_class is None:
                            parent_class, _ = find_class_and_method(callee_name)

                if callee_name:
                    coordinates = CallCoordinates(
                        line=getattr(node, "lineno", -1),
                        char=getattr(node, "col_offset", -1),
                    )
                    calls_list.append(
                        Call(
                            called_file=find_class_and_method(callee_name)[1],
                            caller_class=current_class,
                            caller_func=current_func,
                            parent_class=parent_class,
                            called_func=callee_name,
                            coordinates=coordinates,
                        )
                    )

            # Recurse
            for child in ast.iter_child_nodes(node):
                visit(child, current_class, current_func)

        visit(file_ast, current_class=None, current_func=None)
        return Calls(caller_file=file_meta, calls=calls_list)
