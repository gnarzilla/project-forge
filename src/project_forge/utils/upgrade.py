# src/forge/utils/upgrade.py

import difflib
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import toml
from packaging.version import Version, parse

from .console import console
from .validation import ProjectValidator


@dataclass
class UpgradeChange:
    """Represents a change to be made during upgrade"""

    file: Path
    description: str
    old_content: str
    new_content: str
    priority: int = 1
    breaking: bool = False


class ProjectUpgrader:
    """Handles project upgrades and migrations"""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.validator = ProjectValidator(project_path)
        self.changes: List[UpgradeChange] = []

    def check_upgrades(self) -> bool:
        """Check if project needs upgrades"""
        try:
            # Load current project configuration
            pyproject_path = self.project_path / "pyproject.toml"
            if not pyproject_path.exists():
                console.error("No pyproject.toml found")
                return False

            with open(pyproject_path) as f:
                current_config = toml.load(f)

            # Check Python version constraints
            self._check_python_version(current_config)

            # Check dependencies
            self._check_dependencies(current_config)

            # Check project structure
            self._check_project_structure()

            # Check workflows
            self._check_workflows()

            # Check documentation
            self._check_documentation()

            return len(self.changes) > 0

        except Exception as e:
            console.error(f"Error checking for upgrades: {e}")
            return False

    def perform_upgrade(self, dry_run: bool = False) -> bool:
        """Perform the upgrade"""
        if not self.changes:
            console.info("No upgrades needed")
            return True

        # Sort changes by priority (breaking changes last)
        self.changes.sort(key=lambda x: (x.breaking, x.priority))

        if dry_run:
            self._show_planned_changes()
            return True

        try:
            # Backup project
            if not self._create_backup():
                return False

            # Apply changes
            with console.progress() as progress:
                task = progress.add_task(
                    "Applying upgrades...", total=len(self.changes)
                )

                for change in self.changes:
                    try:
                        if change.breaking:
                            if not console.confirm(
                                f"Apply breaking change: {change.description}?",
                                default=False,
                            ):
                                progress.advance(task)
                                continue

                        change.file.write_text(change.new_content)
                        progress.advance(task)

                    except Exception as e:
                        console.error(f"Failed to apply change to {change.file}: {e}")
                        return False

            # Run post-upgrade actions
            self._run_post_upgrade_actions()

            console.success("Upgrade completed successfully!")
            return True

        except Exception as e:
            console.error(f"Error during upgrade: {e}")
            self._restore_backup()
            return False

    def _check_python_version(self, config: Dict) -> None:
        """Check Python version constraints"""
        current_requires = config.get("project", {}).get("requires-python", "")
        recommended = ">=3.9"

        if current_requires != recommended:
            pyproject_path = self.project_path / "pyproject.toml"
            content = pyproject_path.read_text()
            new_content = content.replace(
                f'requires-python = "{current_requires}"',
                f'requires-python = "{recommended}"',
            )

            self.changes.append(
                UpgradeChange(
                    file=pyproject_path,
                    description="Update Python version constraint",
                    old_content=content,
                    new_content=new_content,
                )
            )

    def _check_dependencies(self, config: Dict) -> None:
        """Check and update dependencies"""
        current_deps = config.get("project", {}).get("dependencies", {})
        dev_deps = (
            config.get("project", {}).get("optional-dependencies", {}).get("dev", {})
        )

        # Define latest known good versions
        recommended_deps = {
            "click": ">=8.0.0",
            "rich": ">=13.0.0",
            "typer": ">=0.9.0",
            "pydantic": ">=2.0.0",
        }

        recommended_dev_deps = {
            "pytest": ">=7.0.0",
            "pytest-cov": ">=4.0.0",
            "black": ">=23.0.0",
            "isort": ">=5.0.0",
            "mypy": ">=1.0.0",
            "pre-commit": ">=3.0.0",
        }

        pyproject_path = self.project_path / "pyproject.toml"
        content = pyproject_path.read_text()
        new_content = content

        # Update main dependencies
        for dep, version in recommended_deps.items():
            if dep in current_deps:
                current_version = current_deps[dep]
                if parse(current_version.lstrip(">=")) < parse(version.lstrip(">=")):
                    new_content = new_content.replace(
                        f'"{dep} = {current_version}"', f'"{dep} = {version}"'
                    )

        # Update dev dependencies
        for dep, version in recommended_dev_deps.items():
            if dep in dev_deps:
                current_version = dev_deps[dep]
                if parse(current_version.lstrip(">=")) < parse(version.lstrip(">=")):
                    new_content = new_content.replace(
                        f'"{dep} = {current_version}"', f'"{dep} = {version}"'
                    )

        if new_content != content:
            self.changes.append(
                UpgradeChange(
                    file=pyproject_path,
                    description="Update dependency versions",
                    old_content=content,
                    new_content=new_content,
                )
            )

    def _check_project_structure(self) -> None:
        """Check and update project structure"""
        required_dirs = {
            "src": "Source code directory",
            "tests": "Test directory",
            "docs": "Documentation directory",
            "examples": "Examples directory",
        }

        for dir_name, description in required_dirs.items():
            dir_path = self.project_path / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True)
                self.changes.append(
                    UpgradeChange(
                        file=dir_path / ".gitkeep",
                        description=f"Create {description}",
                        old_content="",
                        new_content="",
                    )
                )

    def _check_workflows(self) -> None:
        """Check and update GitHub workflows"""
        workflows_dir = self.project_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        workflow_templates = {
            "tests.yml": self._get_tests_workflow(),
            "lint.yml": self._get_lint_workflow(),
            "publish.yml": self._get_publish_workflow(),
        }

        for filename, content in workflow_templates.items():
            workflow_file = workflows_dir / filename
            if not workflow_file.exists():
                self.changes.append(
                    UpgradeChange(
                        file=workflow_file,
                        description=f"Add {filename} workflow",
                        old_content="",
                        new_content=content,
                    )
                )
            else:
                old_content = workflow_file.read_text()
                if old_content != content:
                    self.changes.append(
                        UpgradeChange(
                            file=workflow_file,
                            description=f"Update {filename} workflow",
                            old_content=old_content,
                            new_content=content,
                        )
                    )

    def _check_documentation(self) -> None:
        """Check and update documentation"""
        mkdocs_file = self.project_path / "mkdocs.yml"
        if not mkdocs_file.exists():
            from ..templates.customization import TemplateManager

            template_manager = TemplateManager()
            context = template_manager.get_template_context(
                name=self.project_path.name,
                author="",  # Will be filled from pyproject.toml
                email="",
            )

            # Get author and email from pyproject.toml
            pyproject_path = self.project_path / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path) as f:
                    config = toml.load(f)
                    if "project" in config and "authors" in config["project"]:
                        author_info = config["project"]["authors"][0]
                        context["author"] = author_info.get("name", "")
                        context["email"] = author_info.get("email", "")

            self.changes.append(
                UpgradeChange(
                    file=mkdocs_file,
                    description="Add MkDocs configuration",
                    old_content="",
                    new_content=self._get_mkdocs_template(context),
                )
            )

    def _create_backup(self) -> bool:
        """Create a backup of the project"""
        try:
            backup_dir = self.project_path.parent / f"{self.project_path.name}_backup"
            if backup_dir.exists():
                console.warning(f"Backup directory {backup_dir} already exists")
                if not console.confirm("Override existing backup?", default=False):
                    return False
                shutil.rmtree(backup_dir)

            shutil.copytree(self.project_path, backup_dir)
            console.info(f"Backup created at {backup_dir}")
            return True
        except Exception as e:
            console.error(f"Failed to create backup: {e}")
            return False

    def _restore_backup(self) -> bool:
        """Restore project from backup"""
        backup_dir = self.project_path.parent / f"{self.project_path.name}_backup"
        if not backup_dir.exists():
            console.error("No backup found to restore")
            return False

        try:
            shutil.rmtree(self.project_path)
            shutil.copytree(backup_dir, self.project_path)
            console.success("Project restored from backup")
            return True
        except Exception as e:
            console.error(f"Failed to restore backup: {e}")
            return False

    def _show_planned_changes(self) -> None:
        """Show planned changes in a readable format"""
        console.info("Planned upgrades:", style="bold")

        for i, change in enumerate(self.changes, 1):
            console.print(f"\n{i}. {change.description}")
            if change.breaking:
                console.print("   [red]Breaking change![/]")

            if change.old_content and change.new_content:
                diff = difflib.unified_diff(
                    change.old_content.splitlines(keepends=True),
                    change.new_content.splitlines(keepends=True),
                    fromfile=str(change.file),
                    tofile=str(change.file),
                )
                console.print("   Changes:")
                for line in diff:
                    if line.startswith("+"):
                        console.print(f"   [green]{line}[/]", end="")
                    elif line.startswith("-"):
                        console.print(f"   [red]{line}[/]", end="")
                    else:
                        console.print(f"   {line}", end="")

    def _run_post_upgrade_actions(self) -> None:
        """Run post-upgrade actions"""
        try:
            # Install dependencies
            subprocess.run(
                ["pip", "install", "-e", "."],
                cwd=self.project_path,
                check=True,
                capture_output=True,
            )

            # Setup pre-commit if needed
            if (self.project_path / ".pre-commit-config.yaml").exists():
                subprocess.run(
                    ["pre-commit", "install"],
                    cwd=self.project_path,
                    check=True,
                    capture_output=True,
                )

            # Setup documentation if needed
            if (self.project_path / "mkdocs.yml").exists():
                subprocess.run(
                    [
                        "pip",
                        "install",
                        "mkdocs",
                        "mkdocs-material",
                        "mkdocstrings[python]",
                    ],
                    check=True,
                    capture_output=True,
                )
        except subprocess.CalledProcessError as e:
            console.warning(f"Some post-upgrade actions failed: {e}")

    @staticmethod
    def _get_tests_workflow() -> str:
        """Get content for tests workflow"""
        # Implementation from previous template
        pass

    @staticmethod
    def _get_lint_workflow() -> str:
        """Get content for lint workflow"""
        # Implementation from previous template
        pass

    @staticmethod
    def _get_publish_workflow() -> str:
        """Get content for publish workflow"""
        # Implementation from previous template
        pass

    @staticmethod
    def _get_mkdocs_template(context: Dict) -> str:
        """Get MkDocs template content"""
        # Implementation from previous template
        pass
