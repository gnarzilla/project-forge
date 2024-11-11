# tests/test_config.py

from pathlib import Path

import pytest
from forge.utils.config import ConfigManager


def test_config_creation(temp_dir: Path):
    """Test configuration file creation"""
    config_manager = ConfigManager()
    config_manager.config_dir = temp_dir / ".config" / "forge"
    config_manager.config_file = config_manager.config_dir / "config.yml"

    # Ensure config is created with defaults
    assert config_manager.config is not None
    assert config_manager.config_file.exists()


def test_config_update(config_manager: ConfigManager):
    """Test configuration updates"""
    new_author = "New Author"
    config_manager.update_config(author=new_author)

    assert config_manager.config.author == new_author

    # Ensure persistence
    reloaded = ConfigManager()
    reloaded.config_dir = config_manager.config_dir
    reloaded.config_file = config_manager.config_file
    assert reloaded.load_config().author == new_author


# tests/test_project.py

from pathlib import Path

import pytest
from forge.core.project import ProjectManager


def test_project_creation(project_manager: ProjectManager, temp_dir: Path):
    """Test basic project creation"""
    project_path = project_manager.create_project(
        name="test-project",
        author="Test Author",
        email="test@example.com",
        directory=temp_dir / "test-project",
    )

    assert project_path.exists()
    assert (project_path / "pyproject.toml").exists()
    assert (project_path / "src").exists()
    assert (project_path / "tests").exists()


def test_cli_project_creation(project_manager: ProjectManager, temp_dir: Path):
    """Test CLI project creation"""
    project_path = project_manager.create_project(
        name="test-cli",
        author="Test Author",
        email="test@example.com",
        is_cli=True,
        directory=temp_dir / "test-cli",
    )

    assert project_path.exists()
    assert (project_path / "src" / "cli").exists()
    assert (project_path / "pyproject.toml").exists()

    # Check CLI-specific files
    pyproject_content = (project_path / "pyproject.toml").read_text()
    assert "click" in pyproject_content
    assert "[project.scripts]" in pyproject_content


# tests/test_validation.py

from pathlib import Path

import pytest
from forge.utils.validation import ProjectValidator, validate_project


def test_basic_validation(sample_project: Path):
    """Test basic project validation"""
    validator = ProjectValidator(sample_project)
    assert validator.validate_all()


def test_validation_missing_files(sample_project: Path):
    """Test validation with missing files"""
    # Remove an essential file
    (sample_project / "README.md").unlink()

    validator = ProjectValidator(sample_project)
    assert not validator.validate_all()

    # Check if the correct validation error is present
    readme_errors = [
        r for r in validator.results if "README.md" in r.message and not r.passed
    ]
    assert len(readme_errors) > 0


def test_pyproject_validation(sample_project: Path):
    """Test pyproject.toml validation"""
    validator = ProjectValidator(sample_project)
    validator.validate_pyproject()

    # Should have all required fields
    pyproject_errors = [
        r
        for r in validator.results
        if "pyproject.toml" in r.message and r.severity == "error" and not r.passed
    ]
    assert len(pyproject_errors) == 0


# tests/test_cli.py

from click.testing import CliRunner
from forge.cli.main import cli


def test_forge_command():
    """Test the forge command"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "forge",
                "test-project",
                "--author",
                "Test Author",
                "--email",
                "test@example.com",
            ],
        )
        assert result.exit_code == 0
        assert "Project created" in result.output


def test_inspect_command(sample_project: Path):
    """Test the inspect command"""
    runner = CliRunner()
    result = runner.invoke(cli, ["inspect", str(sample_project)])
    assert result.exit_code == 0
    assert "validation passed" in result.output
