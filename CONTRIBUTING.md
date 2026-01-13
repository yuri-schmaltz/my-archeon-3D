# Contributing to Archeon 3D

Thank you for your interest in contributing! This document outlines our development practices and policies.

## Development Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   
   # Texture generation extensions
   cd hy3dgen/texgen/custom_rasterizer
   python3 setup.py install
   cd ../../..
   cd hy3dgen/texgen/differentiable_renderer
   python3 setup.py install
   ```

2. **Run linter:**
   ```bash
   bash scripts/lint.sh
   ```

## Dependency Management

To add or remove dependencies, modify `requirements.txt` and `setup.py`.

Before committing, ensure that any new dependencies are necessary and don't introduce security risks.

## Repository Hygiene

To maintain a high-quality codebase, we follow these cleanup and organization standards:

1. **Root Cleanliness**: Only essential project files (configs, README, etc.) should belong in the root. Utility scripts go to `scripts/`, tests to `tests/`, and documentation to `docs/`.
2. **Automated Checks**: We provide a script to verify repository governance:
   ```bash
   python scripts/cleanup_governance.py
   ```
3. **Ghost Files**: Avoid committing stubs or "deleted" placeholders. If a file is moved, delete the original completely.
4. **Ignored Files**: Ensure `.gitignore` is up to date and no ignored files (caches, logs, binaries) are accidentally tracked.

## Code Quality

### Pre-commit Checks

We use `pre-commit` to automate code quality checks.

1. **Install pre-commit**: `pip install pre-commit`
2. **Install hooks**: `pre-commit install`
3. **Manual run**: `pre-commit run --all-files`

Local checks still available:
- Linter passes: `ruff check hy3dgen/`
- Governance check: `python scripts/cleanup_governance.py`
- Dependency sync verified: `python scripts/check_dep_sync.py`

### Commit Messages

Use conventional commits format:
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code refactoring
- `chore:` Maintenance tasks
- `docs:` Documentation updates
- `ci:` CI/CD changes

Example:
```
feat: add texture resolution parameter to Paint pipeline

- Add resolution argument to Archeon 3DPaintPipeline
- Update docs with usage examples
- Add tests for resolution validation
```

## Pull Request Process

1. **Create feature branch:** `git checkout -b feature/my-feature`
2. **Make changes** following code quality guidelines
3. **Run checks:** linter, dep sync
4. **Update documentation**
5. **Submit PR** with clear description
6. **Address review feedback**

## CI/CD

Our CI pipeline runs:
- Dependency synchronization check
- Linter validation

All checks must pass before merge.

## Questions?

- Open an issue for bugs or feature requests
- Join our [Discord](https://discord.gg/dNBrdrGGMa) for discussions
- Check existing [documentation](docs/)

Thank you for contributing! 🚀
