# Doti 📦

**Take control of your dotfiles.**

Doti is a powerful, terminal-first tool designed to simplify the management of your configuration files across machines. Stop manually symlinking and worrying about overwriting your precious configs—Doti handles the heavy lifting, backups, and organization for you.

---

## Why Doti?

Managing dotfiles shouldn't feel like a chore. Doti gives you:

* **Safety First:** Automatic backups are created before any symlink is applied. If something goes wrong, your original files are safe.
* **Terminal Native:** No heavy GUIs. Manage everything directly from your CLI with an intuitive interface.
* **Smart Planning:** Review your changes before they happen. Doti calculates an action plan, allowing you to confirm exactly what will be added or removed.
* **Flexible Organization:** Whether you're migrating an existing setup or setting up a fresh machine, Doti keeps your source repo and home directory perfectly in sync.

---

## Getting Started

Doti is designed to be run directly from your terminal.

### Usage

The basic syntax for Doti is:

```bash
doti [action] [options]

```

### Commands

| Action | Description |
| --- | --- |
| `manage` | Open the interactive TUI to select, sync, and manage your configuration files. |
| `migrate` | Move existing local configurations into your dotfile repository. |

### Common Flags

* `-c, --config <FILE>`: Point to a specific configuration file.
* `-s, --source <FILE>`: Explicitly set the path to your dotfiles directory.

---

## Workflow Example

### Managing Your Configs

Want to sync your files? Just run the management command. Doti will visualize your tree and let you select what you want to link:

```bash
doti manage --config ./my_config.yaml

```

1. **Scan:** Doti analyzes your source folder and home directory.
2. **Select:** Use the interactive interface to choose the files/directories you want managed.
3. **Review:** See a clear action plan of what will be symlinked or restored.
4. **Confirm:** Once you approve, Doti applies the changes safely.

---

### Migrating Existing Configs

Have configs already scattered in your home directory? The migrate command finds them and moves them to your dotfiles repository:

```bash
doti migrate --config ./my_config.yaml

```

1. **Scan:** Doti finds all hidden files/directories in your home, including contents of common config directories like `.config`, `.local`, and `Library`.
2. **Select:** Choose which configs you want to migrate.
3. **Migrate:** Doti moves the files to your source directory and creates symlinks back to their original locations.

Example: If you have `~/.bashrc` and `~/.config/nvim/` in your home, running migrate will:
- Move `~/.bashrc` → `dotfiles/.bashrc`
- Move `~/.config/nvim/` → `dotfiles/.config/nvim/`
- Create symlinks at original locations

---

## Installation

### Using uv tool (recommended)
```bash
# Install from git
uv tool install git+https://github.com/anomalyco/doti.git

# Or install locally (for development)
uv tool install -e .

# Or use the Makefile
make install-tool
```

Then run:
```bash
doti --help
```

### From PyPI (when published)
```bash
pip install doti
```

### From source
```bash
# Clone your dotfiles repository
git clone https://github.com/yourusername/dotfiles.git
cd dotfiles

# Install doti in development mode
pip install -e .

# Or install with uv
uv sync
uv pip install -e .
```

### Quick install (latest from main)
```bash
pip install git+https://github.com/anomalyco/doti.git
```
