from dataclasses import dataclass
from typing import Dict, List, Optional

import yaml


@dataclass
class ProjectTemplate:
    name: str
    description: str
    dependencies: List[str]
    structure: Dict[str, List[str]]
    files: Dict[str, str]

    @classmethod
    def from_yaml(cls, path: Path) -> "ProjectTemplate":
        """Load template from YAML file"""
        with path.open() as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: Path):
        """Save template to YAML file"""
        with path.open("w") as f:
            yaml.dump(self.__dict__, f)


# Usage:
templates_dir = Path("templates")
fastapi = ProjectTemplate.from_yaml(templates_dir / "fastapi.yaml")
