# src/forge/templates/hooks.py

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..utils.console import console


class HookStage(Enum):
    PRE_GENERATION = "pre_generation"
    POST_GENERATION = "post_generation"
    PRE_INSTALL = "pre_install"
    POST_INSTALL = "post_install"


@dataclass
class TemplateHook:
    """Defines a hook to be run during project creation"""

    stage: HookStage
    function: Callable
    name: str
    description: Optional[str] = None

    def __call__(self, context: Dict[str, Any], project_path: Path) -> bool:
        """Execute the hook"""
        try:
            console.info(f"Running {self.name}...")
            return self.function(context, project_path)
        except Exception as e:
            console.error(f"Hook {self.name} failed: {e}")
            return False


class TemplateCustomizer:
    """Handles template customization and hooks"""

    def __init__(self):
        self.hooks: Dict[HookStage, List[TemplateHook]] = {
            stage: [] for stage in HookStage
        }
        self._register_default_hooks()

    def _register_default_hooks(self):
        """Register default template hooks"""
        self.register_hook(
            stage=HookStage.POST_GENERATION,
            name="initialize_git",
            function=self._init_git,
            description="Initialize git repository",
        )

        self.register_hook(
            stage=HookStage.POST_GENERATION,
            name="setup_virtual_environment",
            function=self._setup_venv,
            description="Create virtual environment",
        )

        self.register_hook(
            stage=HookStage.POST_INSTALL,
            name="setup_pre_commit",
            function=self._setup_pre_commit,
            description="Configure pre-commit hooks",
        )

        self.register_hook(
            stage=HookStage.POST_INSTALL,
            name="setup_documentation",
            function=self._setup_docs,
            description="Initialize documentation",
        )

    def register_hook(
        self,
        stage: HookStage,
        name: str,
        function: Callable,
        description: Optional[str] = None,
    ):
        """Register a new hook"""
        hook = TemplateHook(stage, function, name, description)
        self.hooks[stage].append(hook)

    def run_hooks(
        self, stage: HookStage, context: Dict[str, Any], project_path: Path
    ) -> bool:
        """Run all hooks for a given stage"""
        success = True
        for hook in self.hooks[stage]:
            if not hook(context, project_path):
                success = False
                console.warning(
                    f"Hook {hook.name} failed, continuing with remaining hooks..."
                )
        return success

    @staticmethod
    def _init_git(context: Dict[str, Any], project_path: Path) -> bool:
        """Initialize git repository"""
        try:
            subprocess.run(
                ["git", "init"], cwd=project_path, check=True, capture_output=True
            )

            # Create initial commit
            subprocess.run(
                ["git", "add", "."], cwd=project_path, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=project_path,
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            console.error(f"Git initialization failed: {e}")
            return False

    @staticmethod
    def _setup_venv(context: Dict[str, Any], project_path: Path) -> bool:
        """Set up virtual environment"""
        try:
            import venv

            venv.create(project_path / "venv", with_pip=True)
            return True
        except Exception as e:
            console.error(f"Virtual environment creation failed: {e}")
            return False

    @staticmethod
    def _setup_pre_commit(context: Dict[str, Any], project_path: Path) -> bool:
        """Set up pre-commit hooks"""
        try:
            subprocess.run(
                ["pip", "install", "pre-commit"],
                cwd=project_path,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["pre-commit", "install"],
                cwd=project_path,
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            console.error(f"Pre-commit setup failed: {e}")
            return False

    @staticmethod
    def _setup_docs(context: Dict[str, Any], project_path: Path) -> bool:
        """Set up documentation"""
        from ..utils.docs import setup_documentation

        return setup_documentation(project_path)
