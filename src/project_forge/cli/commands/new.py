# src/project_forge/cli/commands/new.py

from pathlib import Path

import click

from ...core.project import ProjectManager
from ...utils.console import console


@click.command()
@click.argument("name")
@click.option("--author", help="Project author")
@click.option("--email", help="Author email")
@click.option("--cli", is_flag=True, default=False, help="Create a CLI project")
@click.option(
    "--directory",
    "-d",
    type=click.Path(),
    default=lambda: str(Path.home() / "projects"),
    help="Target directory (defaults to ~/projects)",
)
def new(name: str, author: str, email: str, cli: bool, directory: str):
    """Create a new Python project"""
    try:
        manager = ProjectManager()
        dir_path = Path(directory) / name  # Append project name to directory

        # Create projects directory if it doesn't exist
        dir_path.parent.mkdir(parents=True, exist_ok=True)

        project_path = manager.create_python_package(
            name=name, author=author, email=email, is_cli=cli, directory=dir_path
        )
        console.success(f"Project created successfully at {project_path}")
    except Exception as e:
        console.error(f"Project creation failed: {e}")
        raise click.Abort()
