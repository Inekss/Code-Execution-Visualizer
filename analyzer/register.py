import ast

from models.file import File
from models.registry import RegistryClass, RegistryFile, RegistryFunction


class Register:
    """Builds a Registry from a file's AST."""

    @staticmethod
    def process_node(node, file_node, parent_class=None, parent_function=None):
        """Recursively process AST nodes to populate RegistryFile."""
        if isinstance(node, ast.ClassDef):
            cls_node = RegistryClass(
                class_name=node.name,
                parent_file=file_node,
                parent_class=parent_class,
                parent_function=parent_function,
            )
            for n in node.body:
                Register.process_node(
                    n, file_node, parent_class=cls_node, parent_function=None
                )

            if parent_class:
                parent_class.classes.append(cls_node)
            elif parent_function:
                parent_function.functions.append(cls_node)
            else:
                file_node.classes.append(cls_node)

        elif isinstance(node, ast.FunctionDef):
            func_node = RegistryFunction(
                function_name=node.name,
                parent_file=file_node,
                parent_class=parent_class,
                parent_function=parent_function,
            )
            for n in node.body:
                Register.process_node(
                    n, file_node, parent_class=None, parent_function=func_node
                )

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
