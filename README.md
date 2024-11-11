# Project Forge 🔨

[![CI](https://github.com/gnarzilla/project-forge/actions/workflows/ci.yml/badge.svg)](https://github.com/gnarzilla/project-forge/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/project-forge.svg)](https://badge.fury.io/py/project-forge)
[![codecov](https://codecov.io/gh/gnarzilla/project-forge/branch/main/graph/badge.svg)](https://codecov.io/gh/gnarzilla/project-forge)
[![Documentation Status](https://readthedocs.org/projects/project-forge/badge/?version=latest)](https://project-forge.readthedocs.io/en/latest/?badge=latest)

## Description
A robust Python tool for creating and managing project structures with precision.

## Features

- 🎯 Create standardized Python projects with a single command
- 🧰 Multiple project templates (basic, CLI, and more)
- 📝 Automatic code formatting and structure validation
- ⚡ Smart dependency management and virtual environment setup
- 🔍 Project structure inspection and validation
- 🔄 Built-in upgrade capabilities for existing projects

## Installation

```bash
pip install project-forge
```

## Quick Start

## Usage

### Creating Projects

Create a new Python project:
```bash
project-forge new my-project --author "Your Name" --email "your.email@example.com"
```

Create a CLI project:
```bash
project-forge new my-cli --cli --author "Your Name" --email "your.email@example.com"
```

### Code Formatting
Format code in a project:

```bash
# Check formatting without making changes
project-forge format --check path/to/project

# Format project code
project-forge format path/to/project

# Force formatting on current directory
project-forge format --force .

```
### Project Validation

Check project structure and configuration:

```bash
project-forge check path/to/project

# Check as CLI project
project-forge check path/to/project --type cli

```

## Commands

- `new`: Create a new Python project
- `format`: Format Python code in project
- `check`: Validate project structure and configuration
- `test`: Run project tests
- `upgrade`: Upgrade project structure and dependencies

## Project Structure

Projects created by Project Forge follow this structure:
```bash

my-project/
├── .github/
├── .github/
│   └── workflows/
├── .gitignore
├── src/
│   └── my_project/
│       ├── __init__.py
│       └── core/
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
├── examples/
├── LICENSE
├── README.md
└── pyproject.toml
```

## Configuration

Configure default settings:

### Examples

Projects created by Project-Forge with --cli flag follow this structure:
```bash
$ project-forge new my-cli --cli --author "thatch" --email "gnarzilla@deadlight.boo"
╭─────── Project Creation ────────╮
│ Creating Python package: my-cli │
╰─────────────────────────────────╯

Project Structure:
my-cli/
├── .github/
├── .github/workflows/
├── .gitignore
├── LICENSE
├── README.md
├── docs/
├── examples/
├── pyproject.toml
├── src/
├── src/my_cli/
├── src/my_cli/cli/
└── tests/
✨ Project created successfully at /home/thatch/projects/my-cli
(venv) thatch@thatch:~/Dev/project_forge$ project-forge check ~/projects/my-cli --type cli
Checking cli project structure in /home/thatch/projects/my-cli...
                                       Validation Results                                        
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Status ┃ Message                                   ┃ Details                                  ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ !      │ Empty Examples directory                  │ Add content to: examples/                │
│ !      │ Incomplete README.md                      │ Add section: Description                 │
│ ○      │ Missing recommended pyproject.toml fields │ Consider adding:                         │
│        │                                           │ project.optional-dependencies.dev        │
└────────┴───────────────────────────────────────────┴──────────────────────────────────────────┘
✨ Project validation passed!

```

### Development Setup

1. Clone the repository
```bash
git clone https://github.com/yourusername/project-forge.git
cd project-forge
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies
```bash
pip install -e ".[dev]"
```

4. Run tests
```bash
pytest tests/
```

## License

MIT License - see [LICENSE](LICENSE) for details.
