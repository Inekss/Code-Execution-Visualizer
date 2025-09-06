import ast
from typing import List, Optional, cast

from models.file import File
from models.registry import RegistryClass, RegistryFile, RegistryFunction


class Register:
    """Builds a Registry from a file's AST, including function parameters and type hints."""

    @staticmethod
    def process_node(
        node: ast.AST,
        file_node: RegistryFile,
        parent_class: Optional[RegistryClass] = None,
        parent_function: Optional[RegistryFunction] = None,
    ):
        """Recursively process AST nodes to populate RegistryFile with classes and functions."""

        # --- Handle class definitions ---
        if isinstance(node, ast.ClassDef):
            cls_node = RegistryClass(
                class_name=node.name,
                parent_file=file_node,
                parent_class=parent_class,
                parent_function=parent_function,
            )

            # Recurse into class body
            for n in node.body:
                Register.process_node(
                    n, file_node, parent_class=cls_node, parent_function=None
                )

            # Append to parent
            if parent_class:
                parent_class.classes.append(cls_node)
            elif parent_function:
                parent_function.functions.append(cls_node)
            else:
                file_node.classes.append(cls_node)

        # --- Handle function definitions ---
        elif isinstance(node, ast.FunctionDef):
            params: List[str] = []
            param_types: List[Optional[str]] = []

            # Extract parameter names and type hints
            for arg in node.args.args:
                params.append(arg.arg)
                if arg.annotation is not None:
                    # Cast to ast.AST to satisfy type checkers
                    param_types.append(ast.unparse(cast(ast.AST, arg.annotation)))
                else:
                    param_types.append(None)

            func_node = RegistryFunction(
                function_name=node.name,
                parameters=params,
                param_types=param_types,
                parent_file=file_node,
                parent_class=parent_class,
                parent_function=parent_function,
            )

            # Recurse into function body
            for n in node.body:
                Register.process_node(
                    n, file_node, parent_class=None, parent_function=func_node
                )

            # Append to parent
            if parent_class:
                parent_class.class_functions.append(func_node)
            elif parent_function:
                parent_function.functions.append(func_node)
            else:
                file_node.functions.append(func_node)

    @staticmethod
    def build_registry(data: ast.Module, file_meta: File) -> RegistryFile:
        """Build RegistryFile from an AST and file metadata."""
        file_node = RegistryFile(file=file_meta)
        for node in data.body:
            Register.process_node(node, file_node)
        return file_node
