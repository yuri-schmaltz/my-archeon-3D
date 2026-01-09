# Contributing to Hunyuan3D-2

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

## Code Quality

### Pre-commit Checks

Before committing:
- [ ] Linter passes: `bash scripts/lint.sh`
- [ ] Dependency sync verified: `python scripts/check_dep_sync.py`

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

- Add resolution argument to Hunyuan3DPaintPipeline
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
