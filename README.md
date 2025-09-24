# Code-Execution-Visualizer

**Code Execution Visualizer** is a Python tool for dynamic analysis of Python programs.  
It executes code in an isolated environment (e.g., Docker), analyzes function and class calls, and generates **visualizations** such as:

- Sequence diagrams of function execution  
- Heatmaps of executed lines  
- Function and class dependency graphs  

Designed for **developers and students**, it provides clear insights into program flow and execution behavior.

---

## Classes Overview

### `App`

The **main entry point** of the application.  

**Responsibilities:**

- Initializes the processing pipeline and sets the base path of the code repository.  
- Runs the `Processor` to scan Python files and build a registry of functions, classes, and calls.  
- Saves the dependency roadmap and file hashes to JSON.  
- Uses `VersionProcessor` to compare with previous runs.  
- Builds the **execution graph** using `ExecutionChainBuildProcessor`.  
- Visualizes call chains with `CallChainVisualizer`.  

**Key Methods:**

```python
__init__(base_path: str)  # Sets the root directory for code scanning
run()  # Executes full pipeline: scanning, hashing, building execution chains, visualizing graphs
```

### `Processor`

Handles **static analysis** of Python files and builds the foundational data for execution chains.

---

#### Responsibilities

- Scans all `.py` files in the specified directory recursively.  
- Parses each file’s **Abstract Syntax Tree (AST)** to extract functions, classes, and nested definitions.  
- Builds registries of classes and functions (`RegistryFile`, `RegistryClass`) for later use.  
- Analyzes **imports** to determine module dependencies.  
- Tracks **function calls** across the codebase, even filling in missing file references.  
- Generates a **dependency roadmap** that maps relationships between files, functions, and classes.  

---

#### Key Methods

```python
__init__(base_path: Path)
# Initializes processor with the root path for code scanning

run() -> Tuple[DependencyRoadMap, dict]
# Executes the full processing pipeline:
# 1. Processes each Python file
# 2. Builds registries of classes and functions
# 3. Analyzes imports and calls
# 4. Maps functions/classes to files
# 5. Returns dependency roadmap and file hash dictionary

_process_single_file(py_file: Path, base_path: Path)
    -> Tuple[File, RegistryFile, Imports, Calls, str]
# Processes a single Python file:
# - Reads source code
# - Parses AST
# - Builds registry of classes/functions
# - Analyzes imports
# - Analyzes calls
# - Returns file metadata, registry, imports, calls, and raw source
