# src/project_forge/utils/validation.py

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import toml
import yaml
from rich.table import Table

from .console import console

DEFAULT_PACKAGE_EXCLUDES = {
    '__pycache__',
    'templates',
    'examples',
    'tests',
    'archive',
}

DEFAULT_VALIDATION_DIRS = [
    'src/project_forge',
    'src/project_forge/cli',
    'src/project_forge/cli/commands',
    'src/project_forge/utils',
    'src/project_forge/core'
]


@dataclass
class ValidationResult:
    """Represents the result of a validation check"""

    passed: bool
    message: str
    details: Optional[List[str]] = None
    severity: str = "error"  # error, warning, or info

class ProjectValidator:
    """Validates project structure and configuration"""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.results: List[ValidationResult] = []
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from pyproject.toml"""
        config_path = self.project_path / "pyproject.toml"
        if config_path.exists():
            try:
                pyproject = toml.load(config_path)
                return pyproject.get("tool", {}).get("project-forge", {})
            except Exception as e:
                console.warning(f"Failed to load pyproject.toml config: {e}")
        return {}

    def validate_all(self) -> bool:
        """Run all validation checks"""
        self.validate_structure()
        self.validate_pyproject()
        self.validate_python_packages()
        self.validate_git_setup()
        self.validate_documentation()
        
        # Add template validation
        template_validator = TemplateValidator(self.project_path)
        self.results.extend(template_validator.validate_template())

        self._display_results()

        return all(result.passed for result in self.results if result.severity == "error")

    def validate_structure(self) -> None:
        """Validate project directory structure"""
        essential_dirs = {
            "src": "Source code directory",
            "tests": "Test directory",
            "docs": "Documentation directory",
            "examples": "Examples directory",
        }

        for dir_name, description in essential_dirs.items():
            dir_path = self.project_path / dir_name
            if not dir_path.exists():
                self.results.append(
                    ValidationResult(
                        passed=False,
                        message=f"Missing {description}",
                        details=[f"Create directory: {dir_name}/"],
                        severity="error",
                    )
                )
            elif not any(dir_path.iterdir()):
                self.results.append(
                    ValidationResult(
                        passed=False,
                        message=f"Empty {description}",
                        details=[f"Add content to: {dir_name}/"],
                        severity="warning",
                    )
                )

    def validate_pyproject(self) -> None:
        """Validate pyproject.toml configuration"""
        pyproject_path = self.project_path / "pyproject.toml"

        if not pyproject_path.exists():
            self.results.append(
                ValidationResult(
                    passed=False,
                    message="Missing pyproject.toml",
                    details=["Create pyproject.toml with project configuration"],
                    severity="error",
                )
            )
            return

        try:
            config = toml.load(pyproject_path)

            # Required fields
            required_fields = [
                ("project", "name"),
                ("project", "version"),
                ("project", "description"),
                ("project", "authors"),
                ("project", "dependencies"),
                ("project", "requires-python"),
            ]

            missing_fields = []
            for *path, field in required_fields:
                current = config
                for key in path:
                    if key not in current:
                        missing_fields.append(".".join([*path, field]))
                        break
                    current = current[key]
                else:
                    if field not in current:
                        missing_fields.append(".".join([*path, field]))

            if missing_fields:
                self.results.append(
                    ValidationResult(
                        passed=False,
                        message="Incomplete pyproject.toml",
                        details=[
                            f"Missing required field: {field}"
                            for field in missing_fields
                        ],
                        severity="error",
                    )
                )

            # Recommended fields
            recommended_fields = [
                ("project", "readme"),
                ("project", "license"),
                ("project", "classifiers"),
                ("project", "urls"),
                ("project.optional-dependencies", "dev"),
            ]

            missing_recommended = []
            for *path, field in recommended_fields:
                current = config
                for key in path:
                    if key not in current:
                        missing_recommended.append(".".join([*path, field]))
                        break
                    current = current[key]
                else:
                    if field not in current:
                        missing_recommended.append(".".join([*path, field]))

            if missing_recommended:
                self.results.append(
                    ValidationResult(
                        passed=True,
                        message="Missing recommended pyproject.toml fields",
                        details=[
                            f"Consider adding: {field}" for field in missing_recommended
                        ],
                        severity="warning",
                    )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    passed=False,
                    message="Invalid pyproject.toml",
                    details=[str(e)],
                    severity="error",
                )
            )

    def validate_python_packages(self) -> None:
        """Validate Python package structure"""
        src_path = self.project_path / "src"
        if not src_path.exists():
            return  # Already handled in validate_structure

        # Get configuration or use defaults
        package_excludes = set(self.config.get("package_excludes", DEFAULT_PACKAGE_EXCLUDES))
        validation_dirs = self.config.get("validation_dirs", DEFAULT_VALIDATION_DIRS)


        # Check essential package directories
        missing_init = []
        for dir_path in validation_dirs:
            pkg_dir = self.project_path / dir_path
            if pkg_dir.is_dir() and not (pkg_dir / "__init__.py").exists():
                # Check if directory should be excluded
                if not any(exclude in str(pkg_dir) for exclude in package_excludes):
                    missing_init.append(pkg_dir.relative_to(self.project_path))

        if missing_init:
            self.results.append(
                ValidationResult(
                    passed=False,
                    message="Missing __init__.py files in package directories",
                    details=[f"Create __init__.py in: {path}" for path in missing_init],
                    severity="error"
                )
            )

    def validate_git_setup(self) -> None:
        """Validate Git repository setup"""
        git_dir = self.project_path / ".git"
        gitignore = self.project_path / ".gitignore"

        if not git_dir.exists():
            self.results.append(
                ValidationResult(
                    passed=False,
                    message="Git repository not initialized",
                    details=["Run: git init"],
                    severity="warning",
                )
            )

        if not gitignore.exists():
            self.results.append(
                ValidationResult(
                    passed=False,
                    message="Missing .gitignore",
                    details=["Create .gitignore file with Python-specific patterns"],
                    severity="warning",
                )
            )

    def validate_documentation(self) -> None:
        """Validate documentation setup"""
        docs_path = self.project_path / "docs"
        readme_path = self.project_path / "README.md"

        if not readme_path.exists():
            self.results.append(
                ValidationResult(
                    passed=False,
                    message="Missing README.md",
                    details=["Create README.md with project documentation"],
                    severity="error",
                )
            )
        else:
            # Check README.md content
            content = readme_path.read_text()
            required_sections = ["Description", "Installation", "Usage"]
            missing_sections = [
                section
                for section in required_sections
                if not re.search(rf"#{{1,2}}\s+{section}", content, re.IGNORECASE)
            ]

            if missing_sections:
                self.results.append(
                    ValidationResult(
                        passed=False,
                        message="Incomplete README.md",
                        details=[
                            f"Add section: {section}" for section in missing_sections
                        ],
                        severity="warning",
                    )
                )

    def _display_results(self) -> None:
        """Display validation results in a formatted table"""
        table = Table(title="Validation Results")
        table.add_column("Status", style="cyan", no_wrap=True)
        table.add_column("Message", style="white")
        table.add_column("Details", style="dim")

        status_styles = {
            ("error", True): "[green]✓[/]",
            ("error", False): "[red]✗[/]",
            ("warning", True): "[green]○[/]",
            ("warning", False): "[yellow]![/]",
            ("info", True): "[blue]i[/]",
        }

        for result in sorted(
            self.results, key=lambda x: (x.severity != "error", x.passed)
        ):
            status = status_styles.get((result.severity, result.passed), "?")
            details = "\n".join(result.details) if result.details else ""
            table.add_row(status, result.message, details)

        console.print(table)

@dataclass
class TemplateSpec:
    """Template-specific validation specification"""
    path: str
    description: str
    validators: List[str] = None
    optional: bool = False

@dataclass
class TemplateStructure:
    """Template structure specification"""
    name: str
    description: str
    required_dirs: List[str]
    required_files: Dict[str, TemplateSpec]
    optional_files: Dict[str, TemplateSpec] = None
    inherits: str = None

    @classmethod
    def from_yaml(cls, data: Dict) -> 'TemplateStructure':
        """Create from YAML data"""
        return cls(
            name=data['name'],
            description=data['description'],
            required_dirs=data['required_dirs'],
            required_files={
                path: TemplateSpec(
                    path=path,
                    description=spec['description'],
                    validators=spec.get('validators', [])
                )
                for path, spec in data.get('required_files', {}).items()
            },
            optional_files={
                path: TemplateSpec(
                    path=path,
                    description=spec['description'],
                    validators=spec.get('validators', []),
                    optional=True
                )
                for path, spec in data.get('optional_files', {}).items()
            },
            inherits=data.get('inherits')
        )

class TemplateValidator:
    """Template-specific validation"""
    
    def __init__(self, project_path: Path, template_type: str = "basic"):
        self.project_path = project_path
        self.template_type = template_type
        self.structures = self._load_structures()
        
    def validate_template(self) -> List[ValidationResult]:
        """Validate against template specification"""
        results = []
        structure = self.structures.get(self.template_type)
        if not structure:
            results.append(ValidationResult(
                passed=False,
                message=f"Unknown template type: {self.template_type}",
                severity="error"
            ))
            return results
            
        # Check required directories
        for dir_pattern in structure.required_dirs:
            dir_path = self._resolve_path(self.project_path, dir_pattern)
            if not dir_path.exists() or not dir_path.is_dir():
                results.append(ValidationResult(
                    passed=False,
                    message=f"Missing required directory: {dir_pattern}",
                    severity="error"
                ))

        # Check required files
        for file_pattern, spec in structure.required_files.items():
            file_path = self._resolve_path(self.project_path, file_pattern)
            if not file_path.exists() or not file_path.is_file():
                results.append(ValidationResult(
                    passed=False,
                    message=f"Missing required file: {file_pattern}",
                    details=[spec.description],
                    severity="error"
                ))

        # Check optional files
        if structure.optional_files:
            for file_pattern, spec in structure.optional_files.items():
                file_path = self._resolve_path(self.project_path, file_pattern)
                if not file_path.exists():
                    results.append(ValidationResult(
                        passed=True,
                        message=f"Missing optional file: {file_pattern}",
                        details=[spec.description],
                        severity="info"
                    ))
        
        return results


    def _resolve_path(self, base_path: Path, pattern: str) -> Path:
        """Resolve path pattern with module name"""
        if "{module_name}" in pattern:
            module_name = self._get_module_name(base_path)
            pattern = pattern.format(module_name=module_name)
        return base_path / pattern

    def _get_module_name(self, project_path: Path) -> str:
        """Get module name from pyproject.toml"""
        pyproject_path = project_path / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path) as f:
                data = toml.load(f)
                return data["project"]["name"].replace("-", "_")
        return ""

    def _load_structures(self) -> Dict[str, TemplateStructure]:
        structure_path = Path(__file__).parent.parent / "templates" / "structure.yaml"
        with open(structure_path) as f:
            data = yaml.safe_load(f)
            return {
                name: TemplateStructure.from_yaml(spec)
                for name, spec in data['project_types'].items()
            }

class FileSpec:
    """Specification for a required file"""
    path: str
    description: str
    validators: List[str] = None
    optional: bool = False

@dataclass
class ProjectStructure:
    """Project structure specification"""
    name: str
    description: str
    required_dirs: List[str]
    required_files: Dict[str, FileSpec]
    optional_files: Dict[str, FileSpec] = None
    inherits: str = None

    @classmethod
    def from_yaml(cls, data: Dict) -> 'ProjectStructure':
        """Create from YAML data"""
        return cls(
            name=data['name'],
            description=data['description'],
            required_dirs=data['required_dirs'],
            required_files={
                path: FileSpec(
                    path=path,
                    description=spec['description'],
                    validators=spec.get('validators', [])
                )
                for path, spec in data.get('required_files', {}).items()
            },
            optional_files={
                path: FileSpec(
                    path=path,
                    description=spec['description'],
                    validators=spec.get('validators', []),
                    optional=True
                )
                for path, spec in data.get('optional_files', {}).items()
            },
            inherits=data.get('inherits')
        )

class StructureValidator:
    """Validates project structure against specifications"""

    def __init__(self):
        self.structures: Dict[str, ProjectStructure] = self._load_structures()
        self.validators = {
            'has_valid_name': self._validate_package_name,
            'has_valid_version': self._validate_version,
            'has_title': self._validate_title,
            'has_description': self._validate_description,
            'has_version': self._validate_init_version,
            'has_cli_setup': self._validate_cli_setup
        }

    def _load_structures(self) -> Dict[str, ProjectStructure]:
        """Load structure specifications from YAML"""
        structure_path = Path(__file__).parent.parent / "templates" / "structure.yaml"
        with open(structure_path) as f:
            data = yaml.safe_load(f)
            return {
                name: ProjectStructure.from_yaml(spec)
                for name, spec in data['project_types'].items()
            }

    def check_project(self, project_path: Path, project_type: str = "basic") -> List[str]:
        """Check project structure against specification"""
        if project_type not in self.structures:
            raise ValueError(f"Unknown project type: {project_type}")

        structure = self.structures[project_type]
        issues = []

        # Check directories
        for dir_pattern in structure.required_dirs:
            dir_path = self._resolve_path(project_path, dir_pattern)
            if not dir_path.exists() or not dir_path.is_dir():
                issues.append(f"Missing required directory: {dir_pattern}")

        # Check required files
        for file_pattern, spec in structure.required_files.items():
            file_path = self._resolve_path(project_path, file_pattern)
            if not file_path.exists() or not file_path.is_file():
                issues.append(f"Missing required file: {file_pattern} ({spec.description})")
            elif spec.validators:
                issues.extend(self._validate_file(file_path, spec.validators))

        # Check optional files
        if structure.optional_files:
            for file_pattern, spec in structure.optional_files.items():
                file_path = self._resolve_path(project_path, file_pattern)
                if file_path.exists() and spec.validators:
                    issues.extend(self._validate_file(file_path, spec.validators))

        return issues

    def _resolve_path(self, base_path: Path, pattern: str) -> Path:
        """Resolve path pattern with module name"""
        if "{module_name}" in pattern:
            module_name = self._get_module_name(base_path)
            pattern = pattern.format(module_name=module_name)
        return base_path / pattern

    def _get_module_name(self, project_path: Path) -> str:
        """Get module name from pyproject.toml"""
        pyproject_path = project_path / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path) as f:
                data = toml.load(f)
                return data["project"]["name"].replace("-", "_")
        return ""

    def _validate_file(self, file_path: Path, validators: List[str]) -> List[str]:
        """Run validators on file"""
        issues = []
        for validator in validators:
            if validator in self.validators:
                result = self.validators[validator](file_path)
                if result:
                    issues.append(f"{file_path}: {result}")
        return issues

    # Validator implementations
    def _validate_package_name(self, file_path: Path) -> Optional[str]:
        """Validate package name in pyproject.toml"""
        # Implementation here
        pass

    def _validate_version(self, file_path: Path) -> Optional[str]:
        """Validate version in pyproject.toml"""
        # Implementation here
        pass

    # Add other validators...
