import ast
from typing import Dict, List, Optional

from models.calls import Call, CallCoordinates, Calls
from models.file import File
from models.registry import RegistryClass, RegistryHeap


class CallAnalyzer:
    """
    Analyzes a Python file's AST (Abstract Syntax Tree) to identify function and method calls,
    including which class or function made the call (caller) and which class/function is called (callee).
    """

    @staticmethod
    def analyze_file_ast(
        file_ast: ast.Module,
        file_meta: File,
        registry_heap: RegistryHeap,
        imports_map: Optional[Dict[str, str]] = None,
    ) -> Calls:
        """
        Processes the AST of a single Python file to extract call information.

        Args:
            file_ast: The AST of the Python file.
            file_meta: Metadata about the file (name, path, etc.).
            registry_heap: Registry of all functions/classes in the project.
            imports_map: Optional map of imported names to file paths (for external calls).

        Returns:
            Calls object containing all calls found in the file with coordinates and scope info.
        """
        calls_list: List[Call] = []  # Accumulate all Call objects found
        instance_map: Dict[str, str] = (
            {}
        )  # Track variable instances: var_name -> class_name
        imports_map = imports_map or {}  # Ensure imports_map is a dict

        # --- Helper function: find class/method in the project registry or imports ---
        def find_class_and_method(name: str) -> tuple[Optional[str], Optional[File]]:
            """
            Tries to resolve the called function or class to a class name and file in the project.
            """
            for reg_file in registry_heap.files:
                # Check top-level functions
                for func in reg_file.functions:
                    if func.function_name == name:
                        return None, reg_file.file  # Function is not inside a class

                # Recursively check classes and their methods
                def walk_class(cls: RegistryClass):
                    if cls.class_name == name:
                        return cls.class_name, reg_file.file
                    for f in cls.class_functions:
                        if f.function_name == name:
                            return cls.class_name, reg_file.file
                    for sub_cls in cls.classes:
                        res = walk_class(sub_cls)
                        if res != (None, None):
                            return res
                    return None, None

                for cls in reg_file.classes:
                    res = walk_class(cls)
                    if res != (None, None):
                        return res

            # Fallback: external imports
            if name in imports_map:
                return None, File(
                    file_name=imports_map[name],
                    file_format=".py",
                    file_path=imports_map[name],
                )
            return None, None

        # --- Recursive AST traversal function ---
        def visit(
            node: ast.AST, current_class: Optional[str], current_func: Optional[str]
        ):
            """
            Recursively visits each AST node and tracks the scope to identify calls.

            Args:
                node: Current AST node.
                current_class: Current class scope (if inside a class).
                current_func: Current function/method scope (if inside a function).
            """
            # Update scope if inside class or function
            new_class = current_class
            new_func = current_func
            if isinstance(node, ast.ClassDef):
                new_class = node.name
            elif isinstance(node, ast.FunctionDef):
                new_func = node.name

            # --- Track instance assignments for method calls like `obj = ClassName()` ---
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name):
                    class_name = node.value.func.id
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            instance_map[target.id] = (
                                class_name  # e.g., obj -> ClassName
                            )

            # --- Identify function/method calls ---
            if isinstance(node, ast.Call):
                callee_name = None
                parent_class = None

                # Direct function call: func()
                if isinstance(node.func, ast.Name):
                    callee_name = node.func.id
                    parent_class, _ = find_class_and_method(callee_name)

                # Method or attribute call: obj.method()
                elif isinstance(node.func, ast.Attribute):
                    callee_name = node.func.attr
                    if isinstance(node.func.value, ast.Name):
                        obj_name = node.func.value.id
                        parent_class = instance_map.get(
                            obj_name
                        )  # Check if obj is instance
                        if parent_class is None:
                            parent_class, _ = find_class_and_method(callee_name)

                # Save call info if a callee is identified
                if callee_name:
                    coordinates = CallCoordinates(
                        line=getattr(node, "lineno", -1),
                        char=getattr(node, "col_offset", -1),
                    )
                    calls_list.append(
                        Call(
                            called_file=find_class_and_method(callee_name)[1],
                            caller_class=new_class,  # Class that made the call
                            caller_func=new_func,  # Function that made the call
                            parent_class=parent_class,  # Parent class of callee
                            called_func=callee_name,  # Name of function being called
                            coordinates=coordinates,  # Line/column of call
                        )
                    )

            # Recurse into all child AST nodes
            for child in ast.iter_child_nodes(node):
                visit(child, new_class, new_func)

        # Start AST traversal from the module root
        visit(file_ast, current_class=None, current_func=None)

        # Return all calls found for this file
        return Calls(caller_file=file_meta, calls=calls_list)
