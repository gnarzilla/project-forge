# src/project_forge/cli/__init__.py
import click


@click.group()
def cli():
    """🔨 Project Forge - Craft Python projects with precision"""
    pass


from .commands.check import check
from .commands.format import format_cmd

# Import commands
from .commands.new import new
from .commands.test import test
from .commands.upgrade import upgrade

# Register commands
cli.add_command(new)  # create new project-forge
cli.add_command(test)  # more intuitive than 'temper'
cli.add_command(format_cmd)  # clearer than 'polish'
cli.add_command(check)  # clearer than 'inspect'
cli.add_command(upgrade)
