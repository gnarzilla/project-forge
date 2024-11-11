# src/project_forge/utils/constants.py

"""
Shared constants for project-forge
"""

EXCLUDE_PATTERNS = {
    '__pycache__',
    '*.pyc',
    'venv/',
    '.env/',
    '.git/',
    '*.egg-info/',
    'build/',
    'dist/',
    'archive/',  # Skip archived files
    '*.bak',
    '*.tmp'
}
