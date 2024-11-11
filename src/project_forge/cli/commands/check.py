# src/project_forge/cli/commands/check.py
import sys
import click
from pathlib import Path
from ...utils.validation import ProjectValidator
from ...utils.console import console

@click.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--type', '-t', 'project_type',
              type=click.Choice(['basic', 'cli']),
              default='basic',
              help='Project type to check against')
def check(directory: str, project_type: str):
    """Check project structure and configuration"""
    try:
        project_path = Path(directory)
        validator = ProjectValidator(project_path)
        
        console.info(f"Checking {project_type} project structure in {directory}...")
        
        if not validator.validate_all():
            console.error("Project validation failed")
            sys.exit(1)
            
        console.success("Project validation passed!")
        
    except Exception as e:
        console.error(f"Check failed: {e}")
        sys.exit(1)
