# src/project_forge/cli/commands/test.py

import subprocess
from pathlib import Path

import click

from ...utils.console import console


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--coverage", "-c", is_flag=True, help="Run with coverage report")
def test(path: str, coverage: bool):
    """Run project tests"""
    try:
        import pytest

        console.info(f"Running tests in {path}")

        args = [path, "-v"]
        if coverage:
            args.extend(["--cov", "--cov-report=term-missing"])

        pytest.main(args)

    except ImportError:
        console.error("pytest not installed. Run: pip install pytest pytest-cov")
        raise click.Abort()
    except Exception as e:
        console.error(f"Test execution failed: {e}")
        raise click.Abort()
