# Doti - Agent Configuration

## Project Overview

**Doti** is a Linux dotfile management tool that helps manage configuration files across machines with safety features like automatic backups, interactive TUI, and smart planning.

- **Python version**: 3.12
- **Package manager**: uv
- **Entry point**: `doti` command (defined in pyproject.toml)

## Directory Structure

```
.
├── src/doti/           # Main package source
│   ├── main.py         # CLI entry point
│   ├── core/           # Core modules
│   │   ├── engine.py   # Main Doti engine
│   │   ├── ui.py       # TUI interface
│   │   └── settings.py  # Settings manager
│   ├── utils/          # Utility modules
│   │   └── data.py
│   └── defaults.yaml   # Default configuration
├── tests/              # Test suite
│   ├── test_main.py
│   ├── test_engine.py
│   ├── test_ui.py
│   ├── test_settings.py
│   ├── test_data.py
│   └── test_crossplatform.py
├── playground/         # Test environment
│   ├── home/           # Simulated home directory
│   └── source/         # Simulated dotfile source
├── pyproject.toml     # Project configuration
├── Makefile           # Development commands
└── uv.lock            # Dependency lock file
```

## Installation

### Install with uv (recommended)
```bash
make install        # Install into virtual environment
make install-tool   # Install as uv tool
make install-dev    # Install with dev dependencies
```

### Install with pip
```bash
uv sync
pip install -e .
```

## Commands

### Run the application
```bash
uv run doti [action] [options]
```

Available actions:
- `manage` - Open interactive TUI to select and sync config files
- `migrate` - Move existing local configs into dotfile repository

Common flags:
- `-c, --config <FILE>` - Path to configuration file
- `-s, --source <FILE>` - Path to dotfiles directory

### Run tests
```bash
# Using venv directly (recommended - avoids uv sync issues)
.venv/bin/python -m pytest tests/ -v

# Or using Makefile/uv
make test
uv run pytest tests/ -v
```

### Linting
```bash
make lint
uvx ruff check src/
```

### Build package
```bash
make build
```

## Dependencies

Runtime:
- pyyaml >= 6.0.3
- questionary >= 2.1.1

Dev:
- pytest >= 7.0.0
- build >= 1.0.0
- twine >= 5.0.0
- pip >= 21.0
