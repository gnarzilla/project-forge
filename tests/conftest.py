# tests/conftest.py

import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest
from forge.core.project import ProjectManager
from forge.utils.config import ConfigManager


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a clean temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Provide mock configuration data"""
    return {
        "author": "Test Author",
        "email": "test@example.com",
        "default_type": "python-package",
        "exclude_patterns": [
            "__pycache__",
            "*.pyc",
            ".git/",
            "venv/",
        ],
        "required_dirs": {"python-package": ["src", "tests", "docs", "examples"]},
    }


@pytest.fixture
def config_manager(temp_dir: Path, mock_config: Dict[str, Any]) -> ConfigManager:
    """Provide a configured ConfigManager instance"""
    config_dir = temp_dir / ".config" / "forge"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.yml"

    # Create a config manager with test paths
    manager = ConfigManager()
    manager.config_dir = config_dir
    manager.config_file = config_file
    manager.update_config(**mock_config)

    return manager


@pytest.fixture
def project_manager(config_manager: ConfigManager) -> ProjectManager:
    """Provide a configured ProjectManager instance"""
    manager = ProjectManager()
    manager.config = config_manager
    return manager


@pytest.fixture
def sample_project(project_manager: ProjectManager, temp_dir: Path) -> Path:
    """Create a sample project for testing"""
    project_path = project_manager.create_project(
        name="test-project",
        author="Test Author",
        email="test@example.com",
        directory=temp_dir / "test-project",
    )
    return project_path
