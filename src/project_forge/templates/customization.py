# src/forge/templates/customization.py

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from rich.prompt import Confirm

from ..utils.console import console

@dataclass
class TemplateVariant:
    """Defines a template variant"""

    name: str
    description: str
    dependencies: Dict[str, str]
    features: Dict[str, bool]
    files: Dict[str, str]


class TemplateManager:
    """Manages project templates and customization"""

    def __init__(self, templates_path: Optional[Path] = None):
        self.templates_path = templates_path or Path(__file__).parent
        self.customizer = TemplateCustomizer()
        self.variants: Dict[str, TemplateVariant] = self._load_variants()

    def _load_variants(self) -> Dict[str, TemplateVariant]:
        """Load template variants from configuration"""
        variants_file = self.templates_path / "variants.yml"
        if not variants_file.exists():
            return {}

        with variants_file.open() as f:
            data = yaml.safe_load(f)

        return {
            name: TemplateVariant(**variant_data) for name, variant_data in data.items()
        }

    def get_template_context(
        self,
        name: str,
        author: str,
        email: str,
        description: Optional[str] = None,
        variant: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build template context with optional customization"""
        context = {
            "name": name,
            "author": author,
            "email": email,
            "description": description or f"A Python package for {name}",
            "dependencies": {},
            "features": {},
        }

        if variant and variant in self.variants:
            variant_data = self.variants[variant]
            context["dependencies"].update(variant_data.dependencies)
            context["features"].update(variant_data.features)

        return context

    def customize_project(self, project_path: Path, context: Dict[str, Any]) -> bool:
        """Run project customization process"""
        # Pre-generation hooks
        if not self.customizer.run_hooks(
            HookStage.PRE_GENERATION, context, project_path
        ):
            return False

        # Generate project files
        try:
            self._generate_project_files(project_path, context)
        except Exception as e:
            console.error(f"Project generation failed: {e}")
            return False

        # Post-generation hooks
        if not self.customizer.run_hooks(
            HookStage.POST_GENERATION, context, project_path
        ):
            return False

        # Install dependencies
        if Confirm.ask("Install project dependencies?", default=True):
            if not self.customizer.run_hooks(
                HookStage.PRE_INSTALL, context, project_path
            ):
                return False

            try:
                self._install_dependencies(project_path, context)
            except Exception as e:
                console.error(f"Dependency installation failed: {e}")
                return False

            if not self.customizer.run_hooks(
                HookStage.POST_INSTALL, context, project_path
            ):
                return False

        return True

    def _generate_project_files(self, project_path: Path, context: Dict[str, Any]):
        """Generate project files from templates"""
        # Implementation will be integrated with existing forge.py logic
        pass

    def _install_dependencies(self, project_path: Path, context: Dict[str, Any]):
        """Install project dependencies"""
        # Implementation will be integrated with existing forge.py logic
        pass
