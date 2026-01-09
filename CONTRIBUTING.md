# Contributing to Hunyuan3D-2

Thank you for your interest in contributing! This document outlines our development practices and policies.

## Development Setup

1. **Install dependencies:**
   ```bash
   # Production dependencies
   pip install -r requirements.txt
   pip install -e .
   
   # Development dependencies (testing, linting)
   pip install -r requirements-dev.txt
   
   # Texture generation extensions
   cd hy3dgen/texgen/custom_rasterizer
   python3 setup.py install
   cd ../../..
   cd hy3dgen/texgen/differentiable_renderer
   python3 setup.py install
   ```

2. **Run tests:**
   ```bash
   bash run_tests.sh
   ```

3. **Run linter:**
   ```bash
   bash scripts/lint.sh
   ```

## Multi-Language Documentation Policy

We maintain documentation in three languages:
- **English** (`README.md`) - **Source of truth**
- **Chinese Simplified** (`README_zh_cn.md`)
- **Japanese** (`README_ja_jp.md`)

### Rules

1. **README.md (English) is the authoritative version.** All updates must be reflected here first.

2. **Localized versions must be updated within 48 hours** of changes to `README.md`, or marked as outdated.

3. **If you cannot update localized versions immediately:**
   - Add a notice at the top:
     ```markdown
     > ⚠️ **Outdated**: This version was last updated YYYY-MM-DD. 
     > The [English version](README.md) is more recent.
     ```

4. **For major releases**, all language versions must be synchronized before tagging.

### Pull Request Checklist

When modifying documentation, ensure:

- [ ] `README.md` (English) updated
- [ ] `README_zh_cn.md` updated **OR** marked as outdated
- [ ] `README_ja_jp.md` updated **OR** marked as outdated
- [ ] All code examples tested
- [ ] Links verified

## Dependency Management

### Production vs. Development Dependencies

- **`requirements.txt`**: Production dependencies (API server, model inference, Docker)
- **`requirements-dev.txt`**: Development dependencies (testing, linting, coverage)
- **`setup.py`**: Package installation dependencies (subset of requirements.txt)

### Adding Dependencies

1. **For production code:**
   - Add to `requirements.txt`
   - Add to `setup.py` if needed for package installation
   - Run `python scripts/check_dep_sync.py` to verify sync

2. **For development/testing:**
   - Add to `requirements-dev.txt`

3. **Update lock file** (for reproducible builds):
   ```bash
   pip install -r requirements.txt
   pip freeze > requirements-lock.txt
   ```

### Removing Dependencies

1. Ensure dependency is truly unused:
   ```bash
   grep -r "import <package>" --include="*.py" .
   ```

2. Remove from appropriate file (`requirements.txt` or `requirements-dev.txt`)

3. Verify sync: `python scripts/check_dep_sync.py`

## Code Quality

### Pre-commit Checks

Before committing:
- [ ] Tests pass: `bash run_tests.sh`
- [ ] Linter passes: `bash scripts/lint.sh`
- [ ] No commented-out dependencies in requirements files
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
3. **Run checks:** tests, linter, dep sync
4. **Update documentation** (including localized versions if applicable)
5. **Submit PR** with clear description
6. **Address review feedback**

## CI/CD

Our CI pipeline runs:
- Dependency synchronization check
- All unit tests (`bash run_tests.sh`)
- Docker build validation

All checks must pass before merge.

## Questions?

- Open an issue for bugs or feature requests
- Join our [Discord](https://discord.gg/dNBrdrGGMa) for discussions
- Check existing [documentation](docs/)

Thank you for contributing! 🚀
