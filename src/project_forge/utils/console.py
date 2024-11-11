# src/project_forge/utils/console.py

from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.theme import Theme


class ProjectConsole:
    """Console interface for Project Forge"""

    def __init__(self):
        self.theme = Theme(
            {
                "info": "cyan",
                "success": "green",
                "warning": "yellow",
                "error": "red",
                "highlight": "blue",
            }
        )
        self.console = Console(theme=self.theme)

    def print(
        self, message: Any, title: Optional[str] = None, style: Optional[str] = None
    ):
        """Base print method for all console output"""
        if title:
            self.console.print(
                Panel.fit(str(message), title=title, style=style or "default")
            )
        else:
            self.console.print(message, style=style)

    def info(self, message: str, title: Optional[str] = None):
        """Display information message"""
        self.print(message, title=title, style="info")

    def success(self, message: str, title: Optional[str] = None):
        """Display success message"""
        self.print(f"✨ {message}", title=title, style="success")

    def warning(self, message: str, title: Optional[str] = None):
        """Display warning message"""
        self.print(f"⚠️ {message}", title=title, style="warning")

    def error(self, message: str, title: Optional[str] = None):
        """Display error message"""
        self.print(f"❌ {message}", title=title, style="error")

    def progress(self) -> Progress:
        """Create a progress context"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        )


# Global console instance
console = ProjectConsole()
