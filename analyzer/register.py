import ast
from pathlib import Path

from models.registry import (Registry, RegistryClass, RegistryFile,
                             RegistryFunction)
from utils.reader import Reader


class Register:
    """
    Builds a Registry of Python files, classes, and functions.
    Uses AST to parse Python files and recursively extract classes and functions.
    """

    @staticmethod
    def process_node(node, file_node, parent_class=None, parent_function=None):
        """
        Recursively process an AST node and populate the RegistryFile structure.

        Args:
            node: The current AST node (ast.ClassDef or ast.FunctionDef).
            file_node: The RegistryFile instance representing the current file.
            parent_class: If inside a class, the RegistryClass instance this node belongs to.
            parent_function: If inside a function, the RegistryFunction instance this node belongs to.
        """

        if isinstance(node, ast.ClassDef):
            # Create a RegistryClass for this class
            cls_node = RegistryClass(
                class_name=node.name,
                parent_file=file_node,
                parent_class=parent_class,
                parent_function=parent_function,
            )

            # Recursively process all nodes inside the class body
            for n in node.body:
                Register.process_node(
                    n, file_node, parent_class=cls_node, parent_function=None
                )

            # Attach this class to the correct parent
            if parent_class:
                parent_class.classes.append(cls_node)  # nested class
            elif parent_function:
                parent_function.functions.append(cls_node)  # class inside function
            else:
                file_node.classes.append(cls_node)  # top-level class in file

        elif isinstance(node, ast.FunctionDef):
            # Create a RegistryFunction for this function
            func_node = RegistryFunction(
                function_name=node.name,
                parent_file=file_node,
                parent_class=parent_class,
                parent_function=parent_function,
            )

            # Recursively process any nested functions or classes
            for n in node.body:
                Register.process_node(
                    n, file_node, parent_class=None, parent_function=func_node
                )

            # Attach this function to the correct parent
            if parent_class:
                parent_class.class_functions.append(func_node)  # method of a class
            elif parent_function:
                parent_function.functions.append(func_node)  # nested function
            else:
                file_node.functions.append(func_node)  # top-level function in file

    @staticmethod
    def build_registry(base_path: Path) -> Registry:
        """
        Build a Registry from all Python files under the given base path.

        Args:
            base_path: The root directory to scan for Python files.

        Returns:
            Registry object containing all files, classes, and functions.
        """

        registry = Registry()  # Initialize empty registry

        # Recursively iterate over all Python files
        for py_file in base_path.rglob("*.py"):
            # Parse the file into an AST using Reader
            tree = Reader.parse_file(py_file)

            # Create a RegistryFile instance for this file
            file_node = RegistryFile(
                file_name=py_file.name,
                file_format=py_file.suffix,
                file_path=str(py_file.relative_to(base_path)),
            )

            # Process all top-level nodes (classes/functions) in the file
            for node in tree.body:
                Register.process_node(node, file_node)

            # Add the file to the registry
            registry.files.append(file_node)

        return registry
