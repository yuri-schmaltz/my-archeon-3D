## Description
<!-- Provide a clear and concise description of your changes -->



## Type of Change
<!-- Mark the appropriate option with an 'x' -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🔧 Refactoring (no functional changes)
- [ ] 🎨 Style/formatting changes
- [ ] ⚡ Performance improvement
- [ ] 🧪 Test additions or modifications
- [ ] 🏗️ CI/CD or build tooling changes

## Documentation Checklist
<!-- Required for changes that affect user-facing documentation -->

- [ ] `README.md` (English) updated
- [ ] `README_zh_cn.md` updated **OR** marked as outdated with notice
- [ ] `README_ja_jp.md` updated **OR** marked as outdated with notice
- [ ] Code examples tested and verified
- [ ] API documentation updated (if applicable)

## Dependency Checklist
<!-- Required when adding or modifying dependencies -->

- [ ] Production deps added to `requirements.txt` (if applicable)
- [ ] Dev/test deps added to `requirements-dev.txt` (if applicable)
- [ ] `setup.py` updated (if applicable)
- [ ] Dependency sync verified: `python scripts/check_dep_sync.py`
- [ ] Lock file updated: `pip freeze > requirements-lock.txt` (if needed)

## Testing
<!-- Describe the tests you ran to verify your changes -->

- [ ] All existing tests pass: `bash run_tests.sh`
- [ ] Linter passes: `bash scripts/lint.sh`
- [ ] New tests added (if applicable)
- [ ] Tested on: <!-- e.g., Ubuntu 22.04, Python 3.10 -->

## Checklist
<!-- General checklist for all PRs -->

- [ ] My code follows the project's code style
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Screenshots or Examples
<!-- If applicable, add screenshots or code examples to demonstrate the changes -->



## Breaking Changes
<!-- If this is a breaking change, describe the impact and migration path -->



## Additional Notes
<!-- Any additional information that reviewers should know -->



---

Thank you for your contribution! 🎉
Please ensure all checkboxes are ticked before requesting a review.
