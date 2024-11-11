# src/forge/cli/main.py

from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from ..core.project import ProjectManager
from ..utils.config import ConfigManager
from ..utils.console import console


@click.group()
@click.version_option()
def cli():
    """🔨 Forge - Craft Python projects with precision"""
    pass


@cli.command()
@click.argument("name")
@click.option(
    "--type",
    "project_type",
    type=click.Choice(["python-package"]),
    default="python-package",
    help="Type of project to create",
)
@click.option("--cli/--no-cli", default=False, help="Create a CLI project")
@click.option("--author", help="Project author name")
@click.option("--email", help="Project author email")
@click.option(
    "--directory", "-d", type=click.Path(), help="Target directory for project creation"
)
def forge(
    name: str,
    project_type: str,
    cli: bool,
    author: Optional[str],
    email: Optional[str],
    directory: Optional[str],
):
    """Create a new project"""
    manager = ProjectManager()
    config = ConfigManager()

    # Get author and email from config if not provided
    author = author or config.config.author
    email = email or config.config.email

    if not (author and email):
        console.error(
            "Author and email are required. Either provide them as arguments or "
            "set them in the configuration using 'forge config'"
        )
        return

    try:
        directory_path = Path(directory) if directory else None
        project_path = manager.create_project(
            name=name,
            author=author,
            email=email,
            project_type=project_type,
            is_cli=cli,
            directory=directory_path,
        )
        console.success(f"Project created at: {project_path}")
    except Exception as e:
        console.error(f"Failed to create project: {e}")
        raise click.Abort()


@cli.command()
def config():
    """Configure Forge settings"""
    config_manager = ConfigManager()

    author = click.prompt("Author name", default=config_manager.config.author)
    email = click.prompt("Author email", default=config_manager.config.email)

    config_manager.update_config(author=author, email=email)
    console.success("Configuration updated successfully")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
def temper(path: str):
    """Run tests and checks on the project"""
    try:
        import pytest

        console.info(f"Running tests in {path}")
        pytest.main([path, "-v", "--cov"])
    except ImportError:
        console.error("pytest is not installed. Run: pip install pytest pytest-cov")
        raise click.Abort()


@cli.command()
@click.argument("path", type=click.Path(exists=True))
def polish(path: str):
    """Format and clean the project code"""
    try:
        import black
        import isort

        console.info(f"Formatting code in {path}")

        # Run isort
        isort.main([path])

        # Run black
        black.main([path])

        console.success("Code formatting complete")
    except ImportError:
        console.error("Required formatters not installed. Run: pip install black isort")
        raise click.Abort()


@cli.command()
@click.argument("path", type=click.Path(exists=True))
def inspect(path: str):
    """Check project structure and configuration"""
    manager = ProjectManager()

    try:
        console.info(f"Inspecting project structure in {path}")
        project_path = Path(path)

        # Display project structure
        console.display_tree(project_path, manager.config.config.exclude_patterns)

        # Verify essential files
        essential_files = ["pyproject.toml", "README.md", "LICENSE"]
        missing_files = [f for f in essential_files if not (project_path / f).exists()]

        if missing_files:
            console.warning(f"Missing essential files: {', '.join(missing_files)}")
        else:
            console.success("All essential files present")

    except Exception as e:
        console.error(f"Inspection failed: {e}")
        raise click.Abort()


if __name__ == "__main__":
    cli()
