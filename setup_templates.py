# setup_templates.py

import os
from pathlib import Path

TEMPLATE_DIR = Path("src/project_forge/templates/python/base")

TEMPLATES = {
    "pyproject.toml.j2": """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{{ package_name }}"
version = "0.1.0"
description = "A Python package for {{ name }}"
readme = "README.md"
authors = [{ name = "{{ author }}", email = "{{ email }}" }]
license = { file = "LICENSE" }
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12"
]
dependencies = [
    "rich >= 13.0.0"
]
requires-python = ">=3.9"

[project.optional-dependencies]
dev = [
    "pytest >= 7.0.0",
    "pytest-cov >= 4.0.0",
    "black >= 23.0.0",
    "isort >= 5.0.0",
    "mypy >= 1.0.0"
]

[project.urls]
Homepage = "https://github.com/{{ author }}/{{ package_name }}"
Documentation = "https://{{ package_name }}.readthedocs.io/"
Repository = "https://github.com/{{ author }}/{{ package_name }}.git"
""",
    "README.md.j2": """# {{ name }}

## Description
Add your project description here.

## Installation
```bash
pip install {{ package_name }}
```

## Features
- Feature 1
- Feature 2
- Feature 3

## Usage
```python
from {{ module_name }} import example
# Add usage examples
```

## Development
1. Clone the repository
```bash
git clone https://github.com/{{ author }}/{{ package_name }}.git
cd {{ package_name }}
```

2. Create a virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

3. Run tests
```bash
pytest tests/
```

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
MIT License - see [LICENSE](LICENSE) for details.
""",
    "LICENSE.j2": """MIT License

Copyright (c) {{ year }} {{ author }}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",
    ".gitignore.j2": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.env
.venv
env/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing
.coverage
.pytest_cache/
htmlcov/
.tox/

# Documentation
docs/_build/
site/

# Distribution
dist/
build/

# Project specific
*.log
.DS_Store
""",
}

CLI_TEMPLATES = {
    "pyproject.toml.j2": """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{{ package_name }}"
version = "0.1.0"
description = "A CLI tool for {{ name }}"
readme = "README.md"
authors = [{ name = "{{ author }}", email = "{{ email }}" }]
license = { file = "LICENSE" }
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Environment :: Console"
]
dependencies = [
    "click >= 8.0.0",
    "rich >= 13.0.0"
]
requires-python = ">=3.9"

[project.optional-dependencies]
dev = [
    "pytest >= 7.0.0",
    "pytest-cov >= 4.0.0",
    "black >= 23.0.0",
    "isort >= 5.0.0",
    "mypy >= 1.0.0"
]

[project.scripts]
{{ module_name }} = "{{ module_name }}.cli.main:cli"

[project.urls]
Homepage = "https://github.com/{{ author }}/{{ package_name }}"
Documentation = "https://{{ package_name }}.readthedocs.io/"
Repository = "https://github.com/{{ author }}/{{ package_name }}.git"

[tool.hatch.build.targets.wheel]
packages = ["src/{{ module_name }}"]
""",
    "README.md.j2": """# {{ name }}

A command-line tool for {{ description if description else "doing awesome things" }}.

## Installation

```bash
pip install {{ package_name }}
```

## Usage

```bash
{{ module_name }} --help
```

## Features

- Feature 1
- Feature 2
- Feature 3

## Development

1. Clone the repository
```bash
git clone https://github.com/{{ author }}/{{ package_name }}.git
cd {{ package_name }}
```

2. Create a virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

3. Run tests
```bash
pytest tests/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.
""",
    "src/cli/main.py.j2": '''import click
from rich.console import Console

console = Console()

@click.group()
@click.version_option()
def cli():
    """{{ name }} - Command Line Interface"""
    pass

@cli.command()
def hello():
    """Example command"""
    console.print("[green]Hello from {{ name }}![/]")

if __name__ == "__main__":
    cli()
''',
    "src/cli/__init__.py.j2": '''"""CLI package for {{ name }}"""

from .main import cli

__all__ = ['cli']
''',
}


def setup_templates():
    """Create template files in the correct directory"""
    # Base templates setup (as before)
    base_dir = Path(TEMPLATE_DIR)
    base_dir.mkdir(parents=True, exist_ok=True)

    for filename, content in TEMPLATES.items():
        file_path = base_dir / filename
        with file_path.open("w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created base template: {file_path}")

    # CLI templates setup
    cli_dir = Path("src/project_forge/templates/python/cli")
    cli_dir.mkdir(parents=True, exist_ok=True)

    for filename, content in CLI_TEMPLATES.items():
        file_path = cli_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created CLI template: {file_path}")


if __name__ == "__main__":
    setup_templates()
