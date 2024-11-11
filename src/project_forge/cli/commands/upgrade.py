# src/project_forge/cli/commands/upgrade.py

from pathlib import Path

import click

from ...utils.console import console
from ...utils.upgrade import ProjectUpgrader


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--dry-run", is_flag=True, help="Show planned upgrades without applying them"
)
@click.option(
    "--yes", "-y", is_flag=True, help="Automatically approve all non-breaking changes"
)
def upgrade(path: str, dry_run: bool, yes: bool):
    """Upgrade project structure and dependencies"""
    try:
        project_path = Path(path)
        upgrader = ProjectUpgrader(project_path)

        console.info(f"Checking for upgrades in {project_path}")

        if not upgrader.check_upgrades():
            console.success("Project is up to date!")
            return

        if dry_run:
            upgrader.perform_upgrade(dry_run=True)
            return

        if not yes and not click.confirm("Would you like to proceed with the upgrade?"):
            console.info("Upgrade cancelled")
            return

        if upgrader.perform_upgrade():
            console.success("Project upgraded successfully!")
        else:
            console.error("Project upgrade failed")
            raise click.Abort()

    except Exception as e:
        console.error(f"Error during upgrade: {e}")
        raise click.Abort()
