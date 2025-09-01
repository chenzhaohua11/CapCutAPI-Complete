# Contributing to CapCutAPI

Thank you for your interest in contributing to CapCutAPI! This document provides guidelines and instructions for contributing to the project.

## Getting Started

### Development Environment Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/CapCutAPI.git
   cd CapCutAPI
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow coding standards (see below)
   - Write tests for new functionality
   - Update documentation

3. **Run Tests**
   ```bash
   pytest
   pytest --cov  # With coverage
   ```

4. **Run Quality Checks**
   ```bash
   black .
   isort .
   flake8 .
   mypy .
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Coding Standards

### Python Style Guide

- **Code Formatter**: Black (88 character line length)
- **Import Sorting**: isort
- **Linting**: flake8 with custom rules
- **Type Checking**: mypy (strict mode)
- **Docstrings**: Google style

### File Structure

```
project/
├── src/
│   ├── capcut_server.py
│   ├── settings/
│   └── pyJianYingDraft/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/
├── requirements.txt
└── setup.py
```

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat: add video keyframe support
fix: resolve OSS upload timeout issue
docs: update API documentation
style: format code with black
```

### Testing Guidelines

#### Test Structure

```python
def test_function_name():
    """Test description."""
    # Arrange
    input_data = {...}
    expected = {...}
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected
```

#### Test Categories

- **Unit Tests**: Test individual functions/classes
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete user workflows

#### Running Tests

```bash
# All tests
pytest

# Specific test category
pytest -m unit
pytest -m integration
pytest -m e2e

# With coverage
pytest --cov=capcut_server --cov-report=html

# Verbose output
pytest -v
```

### Documentation Standards

#### Code Documentation
- All public functions must have docstrings
- Include parameter types and return types
- Provide usage examples for complex functions
- Update README.md for new features

#### API Documentation
- Update REST client test files
- Document new endpoints
- Include request/response examples
- Update OpenAPI documentation

## Pull Request Process

### Before Submitting

1. **Tests Pass**
   - All existing tests pass
   - New tests written and passing
   - Coverage maintained or improved

2. **Code Quality**
   - Code formatted with Black
   - Imports sorted with isort
   - No linting errors
   - Type checking passes

3. **Documentation**
   - README updated if needed
   - Docstrings added/updated
   - CHANGELOG.md updated

### PR Template

When creating a PR, please include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Review Process

1. **Automated Checks**
   - CI/CD pipeline runs
   - Security scans pass
   - Code quality checks pass

2. **Code Review**
   - At least one maintainer review
   - Address review feedback
   - Ensure tests cover new functionality

3. **Merge Requirements**
   - All checks must pass
   - PR approved by maintainer
   - Branch up to date with main

## Issue Reporting

### Bug Reports

Include:
- **Environment**: OS, Python version, package versions
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Error messages/logs**

### Feature Requests

Include:
- **Use case description**
- **Proposed solution**
- **Alternative solutions**
- **Additional context**

## Development Tools

### Required Tools
- Python 3.10+
- Git
- Virtual environment (venv or conda)

### Optional Tools
- Docker (for containerized development)
- IDE with Python support (VS Code, PyCharm)
- HTTP client (Postman, curl)

### IDE Configuration

#### VS Code Settings
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true
}
```

## Getting Help

### Resources
- [Documentation](README.md)
- [API Documentation](docs/api.md)
- [Discord Community](https://discord.gg/capcutapi)
- [GitHub Issues](https://github.com/ashreo/CapCutAPI/issues)

### Contact
- **General Questions**: Create GitHub issue with `question` label
- **Security Issues**: Email security@capcutapi.com
- **Feature Requests**: Create GitHub issue with `enhancement` label

## Recognition

Contributors are recognized in:
- [CONTRIBUTORS.md](CONTRIBUTORS.md)
- GitHub contributors page
- Release notes for significant contributions

Thank you for contributing to CapCutAPI! 🎉