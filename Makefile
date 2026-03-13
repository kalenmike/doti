.PHONY: install install-tool install-dev test lint clean

install:
	@echo "Installing doti..."
	@uv pip install -e .

install-tool:
	@echo "Installing doti as uv tool..."
	@uv tool install -e . || echo "Note: If installation fails, try: uv tool install -e . --toolchain system"

install-dev: install
	@echo "Installing dev dependencies..."
	@uv sync --extra dev

test:
	@uv run python -m pytest tests/ -v

lint:
	@uvx ruff check src/

clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache

build:
	@python -m build

publish:
	@twine upload dist/*

help:
	@echo "Available targets:"
	@echo "  install      - Install doti in editable mode"
	@echo "  install-tool - Install doti as uv tool"
	@echo "  install-dev  - Install with dev dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linter"
	@echo "  clean        - Remove build artifacts"
	@echo "  build        - Build package"
	@echo "  publish      - Upload to PyPI"
