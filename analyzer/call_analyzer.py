import ast
from typing import Dict, List, Optional

from models.calls import Call, CallCoordinates, Calls
from models.file import File
from models.registry import RegistryClass, RegistryHeap


class CallAnalyzer:
    """
    Analyzes a Python file's AST to identify function and method calls,
    including caller info, callee info, parameters, and arguments.
    """

    @staticmethod
    def analyze_file_ast(
        file_ast: ast.Module,
        file_meta: File,
        registry_heap: RegistryHeap,
        imports_map: Optional[Dict[str, str]] = None,
    ) -> Calls:
        calls_list: List[Call] = []
        instance_map: Dict[str, str] = {}  # var_name -> class_name
        imports_map = imports_map or {}

        # --- Resolve function/class in registry ---
        def find_class_and_method(
            name: str,
        ) -> tuple[
            Optional[str], Optional[File], Optional[List[str]], Optional[List[str]]
        ]:
            """
            Return (parent_class_name, File, parameters, param_types)
            """
            for reg_file in registry_heap.files:
                # Top-level functions
                for func in reg_file.functions:
                    if func.function_name == name:
                        return (
                            None,
                            reg_file.file,
                            getattr(func, "parameters", None),
                            getattr(func, "param_types", None),
                        )

                # Recursively check classes
                def walk_class(cls: RegistryClass):
                    if cls.class_name == name:
                        return cls.class_name, reg_file.file, None, None
                    for f in getattr(cls, "class_functions", []):
                        if f.function_name == name:
                            return (
                                cls.class_name,
                                reg_file.file,
                                getattr(f, "parameters", None),
                                getattr(f, "param_types", None),
                            )
                    for sub_cls in getattr(cls, "classes", []):
                        res = walk_class(sub_cls)
                        if res != (None, None, None, None):
                            return res
                    return None, None, None, None

                for cls in getattr(reg_file, "classes", []):
                    res = walk_class(cls)
                    if res != (None, None, None, None):
                        return res

            # Fallback to imports
            if name in imports_map:
                f = File(
                    file_name=imports_map[name],
                    file_format=".py",
                    file_path=imports_map[name],
                )
                return None, f, None, None
            return None, None, None, None

        # --- Recursive AST traversal ---
        def visit(
            node: ast.AST, current_class: Optional[str], current_func: Optional[str]
        ):
            global called_file
            new_class = current_class
            new_func = current_func

            if isinstance(node, ast.ClassDef):
                new_class = node.name
            elif isinstance(node, ast.FunctionDef):
                new_func = node.name

            # Track instance assignments: obj = ClassName()
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name):
                    class_name = node.value.func.id
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            instance_map[target.id] = class_name

            # Process calls
            if isinstance(node, ast.Call):
                callee_name = None
                parent_class = None
                parameters, param_types = None, None

                # Direct call: func()
                if isinstance(node.func, ast.Name):
                    callee_name = node.func.id
                    parent_class, called_file, parameters, param_types = (
                        find_class_and_method(callee_name)
                    )

                # Method call: obj.method()
                elif isinstance(node.func, ast.Attribute):
                    callee_name = node.func.attr
                    if isinstance(node.func.value, ast.Name):
                        obj_name = node.func.value.id
                        parent_class = instance_map.get(obj_name)
                        if parent_class is None:
                            parent_class, called_file, parameters, param_types = (
                                find_class_and_method(callee_name)
                            )
                    else:
                        _, called_file, parameters, param_types = find_class_and_method(
                            callee_name
                        )

                # Extract argument values as strings
                arguments = [
                    ast.unparse(arg) if hasattr(ast, "unparse") else None
                    for arg in node.args
                ]

                if callee_name:
                    calls_list.append(
                        Call(
                            called_file=called_file,
                            caller_class=new_class,
                            caller_func=new_func,
                            parent_class=parent_class,
                            called_func=callee_name,
                            coordinates=CallCoordinates(
                                line=getattr(node, "lineno", -1),
                                char=getattr(node, "col_offset", -1),
                            ),
                            parameters=parameters,
                            param_types=param_types,
                            arguments=arguments,
                        )
                    )

            # Recurse
            for child in ast.iter_child_nodes(node):
                visit(child, new_class, new_func)

        visit(file_ast, current_class=None, current_func=None)
        return Calls(caller_file=file_meta, calls=calls_list)
