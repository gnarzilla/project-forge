#!/usr/bin/env python3

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import venv
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Set

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.tree import Tree


class ProjectType(Enum):
    DIRECTORY = "directory"
    PYTHON_PACKAGE = "python-package"


class ProjectManager:
    """Unified project management tool"""

    def __init__(self):
        self.config = ConfigManager()
        self.template_manager = TemplateManager()
        self.console = ForgeConsole()

        # Initialize components
        self.templates_path = Path(__file__).parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_path)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def load_config(self) -> dict:
        """Load or create configuration"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        if self.config_file.exists():
            with self.config_file.open() as f:
                return yaml.safe_load(f) or {}

        # Default configuration
        default_config = {
            "author": "",
            "email": "",
            "default_type": "directory",
            "exclude_patterns": ["__pycache__", "*.pyc", ".git/", "venv/", ".env/"],
            "required_dirs": {
                "python-package": ["src", "tests", "docs", "examples"],
                "directory": ["src", "tests", "docs", "output"],
            },
        }

        with self.config_file.open("w") as f:
            yaml.dump(default_config, f)

        return default_config

    def save_config(self):
        """Save current configuration"""
        with self.config_file.open("w") as f:
            yaml.dump(self.config, f)

    def clean_pycache(self, directory: Path):
        """Remove all __pycache__ directories"""
        for pycache in directory.rglob("__pycache__"):
            shutil.rmtree(pycache)
            print(f"Removed: {pycache}")

    def add_file_to_dirs(self, directory: Path, filename: str) -> int:
        """Add a specified file to all directories"""
        count = 0
        for dir_path in directory.rglob("**/"):
            if dir_path.is_dir() and not any(
                pattern in str(dir_path) for pattern in self.config["exclude_patterns"]
            ):
                file_path = dir_path / filename
                if not file_path.exists():
                    file_path.touch()
                    count += 1
                    print(f"Added {filename} to {dir_path}")
        return count

    def create_python_package(
        self,
        name: str,
        author: str,
        email: str,
        is_cli: bool = False,
        directory: Optional[Path] = None,
    ) -> Path:
        """Create a Python package structure"""
        # Add initial visual feedback
        self.console.print(
            Panel.fit(
                f"Creating Python package: [bold blue]{name}[/]",
                title="Project Creation",
            )
        )

        # Prepare names and paths
        package_name = re.sub(r"[^a-z0-9]+", "-", name.lower())
        module_name = re.sub(r"[^a-z0-9]+", "_", name.lower())
        root = directory or Path(name)

        # Create project structure
        root.mkdir(parents=True, exist_ok=True)

        # Create directories
        dirs = {
            "src": {"module": {"core", "utils"}},
            "tests": {"unit", "integration", "fixtures"},
            "docs": {"api", "guides", "examples"},
            "examples": set(),
            ".github": {"workflows", "ISSUE_TEMPLATE", "PULL_REQUEST_TEMPLATE.md"},
        }

        for dir_name, subdirs in dirs.items():
            base_dir = root / dir_name
            base_dir.mkdir(parents=True, exist_ok=True)
            if isinstance(subdirs, set):
                for subdir in subdirs:
                    if isinstance(subdir, str):
                        (base_dir / subdir).mkdir(parents=True, exist_ok=True)

        # Create __init__.py files
        for py_dir in root.rglob("**/"):
            if py_dir.is_dir() and "src" in str(py_dir):
                (py_dir / "__init__.py").touch()

        # Create essential files
        self._create_package_files(
            root, name, package_name, module_name, author, email, is_cli
        )

        # Show creation success and file tree
        self.console.print("\n✨ Project created successfully!")
        tree = Tree(f"[bold green]{name}/[/]")
        for path in sorted(root.rglob("*")):
            if path.is_file() and not any(
                p in str(path) for p in self.config["exclude_patterns"]
            ):
                rel_path = path.relative_to(root)
                tree.add(f"[blue]{rel_path}[/]")
        self.console.print(tree)

        # Run initialization steps
        self.console.print("\n[bold]Initializing project...[/]")
        initialization_success = self.post_create_actions(root)

        # Show next steps
        steps = [
            "1. cd " + name,
            "2. source venv/bin/activate  # On Windows: venv\\Scripts\\activate",
            "3. pip install -e .",
            "4. pytest tests/",
            "5. Start coding! 🚀",
        ]
        if not initialization_success:
            steps.insert(
                3, "   (Run this if dependencies weren't automatically installed)"
            )

        self.console.print(
            Panel.fit(
                "\n".join(["[green]Next steps:[/]"] + steps), title="Getting Started"
            )
        )

        return root

    def _create_package_files(
        self,
        root: Path,
        name: str,
        package_name: str,
        module_name: str,
        author: str,
        email: str,
        is_cli: bool,
    ):
        """Create all necessary package files"""
        # pyproject.toml
        pyproject_content = self._generate_pyproject_toml(
            package_name, name, author, email, is_cli, module_name
        )
        (root / "pyproject.toml").write_text(pyproject_content)

        # README.md
        readme_content = self._generate_readme(name, package_name)
        (root / "README.md").write_text(readme_content)

        # LICENSE
        license_content = self._generate_license(author)
        (root / "LICENSE").write_text(license_content)

        # .gitignore
        gitignore_content = self._generate_gitignore()
        (root / ".gitignore").write_text(gitignore_content)

        # GitHub workflows
        self._create_github_workflows(root)

        if is_cli:
            self._create_cli_module(root, module_name, name)

    def create_directory_structure(self, directory: Path):
        """Create basic directory structure"""
        required_dirs = self.config["required_dirs"]["directory"]

        for dir_path in required_dirs:
            (directory / dir_path).mkdir(parents=True, exist_ok=True)

        # Add .gitkeep to empty directories
        self.add_file_to_dirs(directory, ".gitkeep")

    def verify_structure(self, directory: Path, project_type: ProjectType) -> list:
        """Verify directory structure"""
        required_dirs = self.config["required_dirs"][project_type.value]
        missing_dirs = []

        for dir_path in required_dirs:
            if not (directory / dir_path).exists():
                missing_dirs.append(dir_path)

        return missing_dirs

    def generate_structure_report(self, directory: Path) -> str:
        """Generate a report of the project structure"""
        report = ["Project Structure Report", "=" * 50, ""]

        for item in sorted(directory.rglob("*")):
            if not any(
                pattern in str(item) for pattern in self.config["exclude_patterns"]
            ):
                depth = len(item.relative_to(directory).parts) - 1
                prefix = "  " * depth + ("📁 " if item.is_dir() else "📄 ")
                report.append(f"{prefix}{item.name}")

        return "\n".join(report)

    def post_create_actions(self, directory: Path):
        """Initialize project after creation"""
        success = True  # Track if all actions completed successfully
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            try:
                # Git initialization
                task = progress.add_task("Initializing git repository...", total=None)
                subprocess.run(
                    ["git", "init"], cwd=directory, capture_output=True, check=True
                )
                progress.update(task, completed=True)

                # Create virtual environment
                task = progress.add_task("Creating virtual environment...", total=None)
                venv.create(directory / "venv", with_pip=True)
                progress.update(task, completed=True)

                # Get the correct pip path based on platform
                if sys.platform == "win32":
                    pip_path = directory / "venv" / "Scripts" / "pip.exe"
                else:
                    pip_path = directory / "venv" / "bin" / "pip"

                # Install dependencies
                if pip_path.exists():
                    task = progress.add_task("Installing dependencies...", total=None)
                    subprocess.run(
                        [str(pip_path), "install", "-e", "."],
                        cwd=directory,
                        capture_output=True,
                        check=True,
                    )
                    progress.update(task, completed=True)
                else:
                    self.console.print(
                        "[yellow]Warning: Could not find pip in virtual environment[/]"
                    )
                    success = False

            except subprocess.CalledProcessError as e:
                self.console.print(f"[red]Error during post-creation: {e}[/]")
                success = False
            except Exception as e:
                self.console.print(f"[yellow]Note: {e}[/]")
                success = False

            return success  # Return success status for the calling method to use

    def _setup_pre_commit_hooks(self, directory: Path):
        """Set up pre-commit hooks for the project"""
        hooks_dir = directory / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        pre_commit_hook = hooks_dir / "pre-commit"
        pre_commit_content = """#!/bin/sh
	# Run code formatting check
	if command -v black >/dev/null 2>&1; then
	    black --check .
	fi
	
	# Run tests
	if command -v pytest >/dev/null 2>&1; then
	    pytest tests/
	fi
	"""
        pre_commit_hook.write_text(pre_commit_content)
        pre_commit_hook.chmod(0o755)

    def verify_project(self, directory: Path) -> bool:
        """Verify project structure and setup"""
        issues = []

        # Check essential files
        essential_files = ["pyproject.toml", "README.md", "LICENSE", ".gitignore"]

        for file in essential_files:
            if not (directory / file).exists():
                issues.append(f"Missing {file}")

        # Check virtual environment
        if not (directory / "venv").exists():
            issues.append("Virtual environment not found")

        # Check git initialization
        if not (directory / ".git").exists():
            issues.append("Git not initialized")

        # Report issues
        if issues:
            self.console.print("[red]Project verification failed:[/]")
            for issue in issues:
                self.console.print(f"❌ {issue}")
            return False

        self.console.print("[green]Project verification passed! ✨[/]")
        return True

    # Helper methods for file generation
    def _generate_pyproject_toml(
        self, package_name, name, author, email, is_cli, module_name
    ):
        """Generate pyproject.toml content"""
        content = f"""[build-system]
	requires = ["hatchling"]
	build-backend = "hatchling.build"
	
	[project]
	name = "{package_name}"
	version = "0.1.0"
	description = "A Python package for {name}"
	readme = "README.md"
	authors = [{{ name = "{author}", email = "{email}" }}]
	license = {{ file = "LICENSE" }}
	classifiers = [
	"Development Status :: 3 - Alpha",
	"Intended Audience :: Developers",
	"License :: OSI Approved :: MIT License",
	"Programming Language :: Python :: 3",
	"Programming Language :: Python :: 3.9",
	"Programming Language :: Python :: 3.10",
	"Programming Language :: Python :: 3.11",
    	"Programming Language :: Python :: 3.12",
	]
	dependencies = [
    	"click >= 8.0.0",
	]
	requires-python = ">=3.9"
	
	[project.optional-dependencies]
	dev = [
    	"pytest >= 7.0.0",
    	"pytest-cov >= 4.0.0",
    	"black >= 23.0.0",
    	"isort >= 5.0.0",
	]
	
	[project.urls]
	Homepage = "https://github.com/{author}/{package_name}"
	Documentation = "https://{package_name}.readthedocs.io/"
	Repository = "https://github.com/{author}/{package_name}.git"
	"""
        if is_cli:
            content += f"""
	[project.scripts]
	{module_name} = "{module_name}.cli:main"
	"""
        return content

    def _generate_readme(self, name, package_name):
        """Generate README.md content"""
        return f"""# {name}

	## Description

	Add your project description here.
	
	## Installation
	
	```bash
	pip install {package_name}
	```
	
	## Usage
	
	```python
	from {package_name} import example
	
	# Add usage examples
	```

	## Contributing
	
	See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
	
	## License
	
	MIT License - see [LICENSE](LICENSE) for details.
	"""

    def _generate_license(self, author):
        """Generate LICENSE content"""
        year = datetime.now().year
        return f"""MIT License
	
	Copyright (c) {year} {author}
	
	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:
	
	The above copyright notice and this permission notice shall be included in all
	copies or substantial portions of the Software.
	
	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
	SOFTWARE.
	"""

    def _generate_gitignore(self):
        """Generate .gitignore content"""
        return """# Python
	__pycache__/
	*.py[cod]
	*$py.class
	*.so
	.Python
	build/
	develop-eggs/
	dist/
	downloads/
	eggs/
	.eggs/
	lib/
	lib64/
	parts/
	sdist/
	var/
	wheels/
	*.egg-info/
	.installed.cfg
	*.egg
	
	# Virtual Environment
	.env
	.venv
	env/
	venv/
	ENV/
	
	# IDE
	.idea/
	.vscode/
	*.swp
	*.swo
	
	# Testing
	.coverage
	.pytest_cache/
	htmlcov/
	
	# Documentation
	docs/_build/
	"""

    def _create_github_workflows(self, root: Path):
        """Create GitHub workflow files"""
        workflow_dir = root / ".github" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        # Create test workflow
        test_workflow = """name: Tests

	on:
	  push:
	    branches: [ main ]
	  pull_request:
	    branches: [ main ]

	jobs:
	  test:
	    runs-on: ubuntu-latest
	    strategy:
	      matrix:
	        python-version: ["3.9", "3.10", "3.11", "3.12"]

	    steps:
	    - uses: actions/checkout@v3
	    - name: Set up Python ${{ matrix.python-version }}
	      uses: actions/setup-python@v4
	      with:
	        python-version: ${{ matrix.python-version }}
	    - name: Install dependencies
	      run: |
	        python -m pip install --upgrade pip
	        pip install .[dev]
	    - name: Run tests
	      run: |
	        pytest --cov
	"""
        (workflow_dir / "tests.yml").write_text(test_workflow)

    def _create_cli_module(self, root: Path, module_name: str, name: str):
        """Create CLI module files"""
        cli_dir = root / "src" / module_name / "cli"
        cli_dir.mkdir(parents=True, exist_ok=True)

        # Create main CLI file
        cli_content = f'''import click
	
	@click.group()
	def cli():
	    """{name} command line interface"""
	    pass
	
	@cli.command()
	def hello():
	    """Say hello"""
	    click.echo("Hello from {name}!")
	
	def main():
	    cli()
	
	if __name__ == '__main__':
	    main()
	'''
        (cli_dir / "__init__.py").write_text(cli_content)


def main():
    parser = argparse.ArgumentParser(
        description="🔨 Project Forge - Craft Python projects with precision"
    )

    # Common arguments
    parser.add_argument(
        "--config", action="store_true", help="Configure default settings"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Forge command (create)
    forge_parser = subparsers.add_parser("forge", help="Create a new project")
    forge_parser.add_argument("name", help="Name of the project")
    forge_parser.add_argument(
        "--type",
        choices=["python-package"],
        default="python-package",
        help="Type of project",
    )
    forge_parser.add_argument("--cli", action="store_true", help="Create a CLI package")
    forge_parser.add_argument("--author", help="Author name")
    forge_parser.add_argument("--email", help="Author email")

    # Temper command (test)
    temper_parser = subparsers.add_parser("temper", help="Run tests and checks")
    temper_parser.add_argument("path", help="Path to project")

    # Polish command (format)
    polish_parser = subparsers.add_parser("polish", help="Format and clean code")
    polish_parser.add_argument("path", help="Path to project")

    # Inspect command (check)
    inspect_parser = subparsers.add_parser("inspect", help="Check project structure")
    inspect_parser.add_argument("path", help="Path to project")

    args = parser.parse_args()
    manager = ProjectManager()

    try:
        if args.config:
            # Interactive configuration
            author = input(
                f"Author name [{manager.config.get('author', '')}]: "
            ).strip()
            email = input(f"Author email [{manager.config.get('email', '')}]: ").strip()

            if author:
                manager.config["author"] = author
            if email:
                manager.config["email"] = email

            manager.save_config()
            print("✅ Configuration updated successfully")
            return

        if args.command == "forge":
            if not args.name:
                parser.error("Project name is required")

            author = args.author or manager.config.get("author")
            email = args.email or manager.config.get("email")

            if not (author and email):
                parser.error(
                    "Author and email are required. Use --config to set defaults."
                )

            path = manager.create_python_package(args.name, author, email, args.cli)
            print(f"✨ Project created at {path}")

        elif args.command == "temper":
            directory = Path(args.path)
            print(f"Running tests for {directory}...")
            # TODO: Implement testing

        elif args.command == "polish":
            directory = Path(args.path)
            print(f"Formatting code in {directory}...")
            # TODO: Implement formatting

        elif args.command == "inspect":
            directory = Path(args.path)
            print(f"Checking project structure in {directory}...")
            missing = manager.verify_structure(directory, ProjectType.PYTHON_PACKAGE)
            if missing:
                print("Missing components:", missing)
            else:
                print("✅ Project structure is complete")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    main()
