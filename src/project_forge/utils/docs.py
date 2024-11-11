# src/forge/utils/docs.py

import subprocess
from pathlib import Path
from typing import Optional

from .console import console


def setup_documentation(project_path: Path) -> bool:
    """Set up documentation for the project"""
    try:
        # Install mkdocs and theme if not present
        subprocess.run(
            ["pip", "install", "mkdocs", "mkdocs-material", "mkdocstrings[python]"],
            check=True,
            capture_output=True,
        )

        # Initialize mkdocs if not already initialized
        if not (project_path / "mkdocs.yml").exists():
            subprocess.run(
                ["mkdocs", "new", "."],
                cwd=project_path,
                check=True,
                capture_output=True,
            )

        # Create docs directory structure
        docs_dirs = ["guides", "api", "examples"]

        docs_path = project_path / "docs"
        for dir_name in docs_dirs:
            (docs_path / dir_name).mkdir(parents=True, exist_ok=True)

        console.success("Documentation setup complete")
        console.info(
            "To serve documentation locally:\n"
            "1. cd " + str(project_path) + "\n"
            "2. mkdocs serve\n"
            "3. Open http://127.0.0.1:8000 in your browser"
        )

        return True

    except subprocess.CalledProcessError as e:
        console.error(f"Failed to set up documentation: {e}")
        return False
    except Exception as e:
        console.error(f"Error during documentation setup: {e}")
        return False
