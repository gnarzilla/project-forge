# src/project_forge/cli/commands/format.py

import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Set, Union
from ...utils.constants import EXCLUDE_PATTERNS

import click

from ...utils.console import console


class CodeFormatter:
    """Code formatting utility for Python projects"""

    def __init__(self, verbose: bool = False, include_empty: bool = False):
        self.verbose = verbose
        self.include_empty = include_empty
        self.exclude_patterns = EXCLUDE_PATTERNS

    def _find_python_files(self, path: Path) -> List[Path]:
        """Find Python files to format"""
        if path.is_file():
            return [path] if path.suffix == '.py' else []
        
        # If it's a directory, find all Python files
        return [
            f for f in path.rglob('*.py')
            if not any(pattern in str(f) for pattern in self.exclude_patterns)
        ]

    def _format_file(self, file_path: Path, verbose: bool = False):
        """Format a single file"""
        import black
        import isort

        try:
            # Check if file exists and is readable
            if not file_path.exists():
                raise click.ClickException(f"File not found: {file_path}")

            # Handle empty files
            if file_path.stat().st_size == 0 and not self.include_empty:
                console.info(f"Skipping empty file: {file_path}")
                return

            # Format imports
            isort.file(str(file_path))  # Convert Path to string for isort

            # Read and format content
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Skip empty or whitespace-only files
                if not content.strip():
                    console.info(f"Skipping empty file: {file_path}")
                    return

                # Check for lines starting with @, @click, etc.
                if any(line.startswith(('@', '@click')) for line in content.splitlines()):
                    console.info(f"Skipping file with decorator lines: {file_path}")
                    return

                formatted = black.format_file_contents(
                    content,
                    fast=False,
                    mode=black.FileMode(),
                )

                # Only write if changes were made
                if formatted != content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(formatted)
                    console.info(f"Formatted: {file_path}")
                else:
                    console.info(f"Already formatted: {file_path}")

            except black.InvalidInput as e:
                if self.verbose:
                    console.error(
                        f"Invalid Python code in {file_path}: {str(e)}"
                    )
                raise click.ClickException(str(e))

        except Exception as e:
            console.error(f"Failed to format {file_path}: {str(e)}")
            raise click.ClickException(str(e))

    def check_files(self, paths: List[Union[Path, str]], verbose: bool = False) -> bool:
        """Check the formatting of the specified files or directories"""
        success = True
        for path in paths:
            path = Path(path)
            if path.is_file():
                try:
                    result = self._check_file(path, verbose=verbose)
                    if not result:
                        success = False
                except Exception as e:
                    console.error(f"Error checking {path}: {e}")
                    success = False
            elif path.is_dir():
                for file_path in self._find_python_files(path):
                    try:
                        result = self._check_file(file_path, verbose=verbose)
                        if not result:
                            success = False
                    except Exception as e:
                        console.error(f"Error checking {file_path}: {e}")
                        success = False
            else:
                console.error(f"Invalid path: {path}")
                success = False
        return success

    def format_files(self, paths: List[Union[Path, str]], verbose: bool = False) -> bool:
        """Format the specified files or directories"""
        success = True
        for path in paths:
            path = Path(path)
            if path.is_file():
                try:
                    self._format_file(path, verbose=verbose)
                except Exception as e:
                    console.error(f"Error formatting {path}: {e}")
                    success = False
            elif path.is_dir():
                for file_path in self._find_python_files(path):
                    try:
                        self._format_file(file_path, verbose=verbose)
                    except Exception as e:
                        console.error(f"Error formatting {file_path}: {e}")
                        success = False
            else:
                console.error(f"Invalid path: {path}")
                success = False
        return success

    def _check_file(self, file_path: Path, verbose: bool = False) -> bool:
        """Check if a file needs formatting"""
        import black
        import isort

        # Check imports
        if not isort.check_file(file_path):
            console.warning(f"Imports need sorting in {file_path}")
            return False

        # Check formatting
        with open(file_path, "rb") as f:
            content = f.read()

        try:
            black.format_file_contents(
                content.decode(),
                fast=False,
                mode=black.FileMode(),
            )
            return True
        except black.InvalidInput:
            if verbose:
                console.error(f"Invalid Python code in {file_path}")
            return False
        except black.NothingChanged:
            return True
        except Exception:
            if verbose:
                console.warning(f"Formatting needed in {file_path}")
            return False

def format_project(self, paths: List[Path], check_only: bool = False, fix: bool = False, verbose: bool = False) -> bool:
    """Format the specified Python files"""
    with console.progress() as progress:
        # Setup formatters
        task = progress.add_task("Setting up formatters...", total=None)
        try:
            import black
            import isort
            progress.update(task, completed=True)
        except ImportError:
            console.error("Required formatters not installed. Installing...")
            self._install_formatters()
            progress.update(task, completed=True)

        # Format files
        task = progress.add_task("Formatting files...", total=len(paths))
        successfully_formatted: List[Path] = []
        failed_to_format: List[Path] = []

        for file_path in paths:
            try:
                if check_only:
                    result = self._check_file(file_path, verbose=verbose)
                    if not result:
                        failed_to_format.append(file_path)
                elif fix:
                    self._format_file(file_path, verbose=verbose)
                    successfully_formatted.append(file_path)
                else:
                    console.print(
                        "Please use either --check-only or --fix to specify the desired operation."
                    )
                    sys.exit(1)
                progress.advance(task)
            except Exception as e:
                console.error(f"Error processing {file_path}: {e}")
                failed_to_format.append(file_path)

        # Print formatting summary
        if check_only:
            if not failed_to_format:
                console.success("All files are properly formatted!")
            else:
                console.print(f"\n{len(failed_to_format)} files need formatting:")
                for file_path in failed_to_format:
                    console.print(f"- {file_path}")
                    if verbose:
                        console.print_formatted_text(
                            self._get_diff(file_path), style="diff"
                        )
        else:
            console.print(f"\n✨ Formatting complete! {len(successfully_formatted)} files formatted.")
            if failed_to_format:
                console.print(f"\n❌ {len(failed_to_format)} files could not be formatted:")
                for file_path in failed_to_format:
                    console.print(f"- {file_path}")

    return len(failed_to_format) == 0

    def _find_python_files(self, path: Path) -> List[Path]:
        """Find Python files to format"""
        if path.is_file():
            return [path] if path.suffix == '.py' else []
        
        # If it's a directory, find all Python files
        return [
            f for f in path.rglob('*.py')
            if not any(pattern in str(f) for pattern in self.exclude_patterns)
        ]


    def _install_formatters(self):
        """Install required formatting tools"""
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "black", "isort"],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise click.ClickException(
                f"Failed to install formatters: {e.stderr.decode()}"
            )

    def _get_diff(self, file_path: Path) -> str:
        """Generate a colorized diff for the given file"""
        import black

        with open(file_path, "r") as f:
            original_content = f.read()

        try:
            formatted = black.format_file_contents(
                original_content,
                fast=False,
                mode=black.FileMode(),
            )
        except black.InvalidInput:
            return f"Error: Invalid Python code in {file_path}"

        if formatted == original_content:
            return "No formatting changes needed."
        else:
            from rich.syntax import Syntax

            diff = Syntax.diff(original_content, formatted, line_numbers=True, word_wrap=True)
            return diff

    def check_files(self, paths: List[Union[Path, str]], verbose: bool = False) -> bool:
        """Check the formatting of the specified files or directories"""
        success = True
        for path in paths:
            path = Path(path)
            if path.is_file():
                try:
                    result = self._check_file(path, verbose=verbose)
                    if not result:
                        success = False
                except Exception as e:
                    console.error(f"Error checking {path}: {e}")
                    success = False
            elif path.is_dir():
                for file_path in self._find_python_files(path)[0]:
                    try:
                        result = self._check_file(file_path, verbose=verbose)
                        if not result:
                            success = False
                    except Exception as e:
                        console.error(f"Error checking {file_path}: {e}")
                        success = False
            else:
                console.error(f"Invalid path: {path}")
                success = False
        return success

def format_files(self, paths: List[Union[Path, str]], verbose: bool = False) -> bool:
    """Format the specified files or directories"""
    success = True
    for path in paths:
        path = Path(path)
        if path.is_file():
            try:
                self._format_file(path, verbose=verbose)
            except Exception as e:
                console.error(f"Error formatting {path}: {e}")
                success = False
        elif path.is_dir():
            for file_path in self._find_python_files(path)[0]:
                try:
                    self._format_file(file_path, verbose=verbose)
                except Exception as e:
                    console.error(f"Error formatting {file_path}: {e}")
                    success = False
        else:
            console.error(f"Invalid path: {path}")
            success = False
    return success

@click.command(name="format")
@click.argument("files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--check-only",
    is_flag=True,
    default=False,
    help="Check formatting without making changes",
)
@click.option(
    "--fix",
    is_flag=True,
    default=False,
    help="Apply formatting changes to files",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Show detailed error messages",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force operation on root/current directory",
)
def format_cmd(files, check_only: bool = False, fix: bool = False, verbose: bool = False, force: bool = False):
    """Format Python code in project"""
    try:
        if files:
            paths = [Path(f) for f in files]
        else:
            path = Path(directory).resolve()
            # Safety checks for directory-level operations
            if path == Path("/") and not force:
                console.error(
                    "Refusing to run on root directory. Use --force if you really want to do this."
                )
                sys.exit(1)
            if path == Path.cwd() and not force:
                console.error(
                    "Refusing to run on current directory. Either specify a project directory "
                    "or use --force if you really want to format here."
                )
                sys.exit(1)
            paths = self._find_python_files(path)[0]

        formatter = CodeFormatter(verbose=verbose)
        if check_only:
            success = formatter.check_files(paths, verbose=verbose)
            if not success:
                sys.exit(1)
        elif fix:
            success = formatter.format_files(paths, verbose=verbose)
        else:
            console.print(
                "Please use either --check-only or --fix to specify the desired operation."
            )
            sys.exit(1)
    except click.ClickException as e:
        console.error(str(e))
        sys.exit(1)
    except Exception as e:
        console.error(f"Formatting failed: {e}")
        sys.exit(1)