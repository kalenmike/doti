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
│   │   └── settings.py # Settings manager
│   └── utils/          # Utility modules
│       └── data.py
├── playground/         # Test environment
│   ├── home/           # Simulated home directory
│   └── source/         # Simulated dotfile source
├── pyproject.toml      # Project configuration
└── uv.lock            # Dependency lock file
```

## Commands

### Install dependencies
```bash
uv sync
```

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

### Type checking
```bash
uv run pyright
```

### Linting
```bash
uv run ruff check
```

## Dependencies

- pyyaml >= 6.0.3
- questionary >= 2.1.1
