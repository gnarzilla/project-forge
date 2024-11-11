# src/forge/utils/config.py

from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    author: str = Field("", description="Default project author")
    email: str = Field("", description="Default author email")
    default_type: str = Field("directory", description="Default project type")
    exclude_patterns: list[str] = Field(
        default_factory=lambda: ["__pycache__", "*.pyc", ".git/", "venv/", ".env/"]
    )
    required_dirs: Dict[str, list[str]] = Field(
        default_factory=lambda: {
            "python-package": ["src", "tests", "docs", "examples"],
            "directory": ["src", "tests", "docs", "output"],
        }
    )


class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "project-manager"
        self.config_file = self.config_dir / "config.yml"
        self.config = self.load_config()

    def load_config(self) -> ProjectConfig:
        """Load or create configuration"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        if self.config_file.exists():
            with self.config_file.open() as f:
                config_data = yaml.safe_load(f) or {}
        else:
            config_data = {}

        return ProjectConfig(**config_data)

    def save_config(self):
        """Save current configuration"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with self.config_file.open("w") as f:
            yaml.dump(self.config.model_dump(), f)

    def update_config(self, **kwargs):
        """Update configuration with new values"""
        config_data = self.config.model_dump()
        config_data.update(kwargs)
        self.config = ProjectConfig(**config_data)
        self.save_config()
