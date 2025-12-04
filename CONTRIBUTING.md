# Contributing to MCP Energy Hub

Thank you for your interest in contributing to MCP Energy Hub! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/mcp-energy-hub.git
   cd mcp-energy-hub
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/original-owner/mcp-energy-hub.git
   ```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- [EIA API Key](https://www.eia.gov/opendata/register.php) (free)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov black isort flake8 mypy

# Copy environment file
cp .env.example .env
# Edit .env with your configuration
```

### Running Locally

```bash
# Start the FastAPI server
python -m uvicorn app.main:app --reload --port 8000

# Run the MCP server
python mcp_server.py
```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

When creating a bug report, include:
- **Clear title** describing the issue
- **Steps to reproduce** the behavior
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, etc.)
- **Relevant logs** or error messages

### Suggesting Features

Feature requests are welcome! Please include:
- **Clear description** of the feature
- **Use case** explaining why it's needed
- **Proposed implementation** (if you have ideas)

### Contributing Code

1. **Find an issue** to work on, or create one
2. **Comment on the issue** to let others know you're working on it
3. **Create a branch** for your work:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```
4. **Make your changes** following our coding standards
5. **Write tests** for your changes
6. **Submit a pull request**

## Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass**:
   ```bash
   pytest
   ```
4. **Format your code**:
   ```bash
   black .
   isort .
   ```
5. **Update the README** if you've added features
6. **Create the PR** with a clear description

### PR Title Format

Use conventional commit format:
- `feat: add new MCP tool for solar data`
- `fix: correct carbon calculation formula`
- `docs: update installation instructions`
- `refactor: simplify grid region handling`
- `test: add tests for EIA collector`

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Maximum line length: 88 characters (Black default)

### Code Quality

```bash
# Format code
black .
isort .

# Check linting
flake8 .

# Type checking
mypy app/
```

### Naming Conventions

- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Files**: `snake_case.py`

### Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings:
  ```python
  def get_carbon_intensity(region_id: str) -> float:
      """Get the carbon intensity for a grid region.
      
      Args:
          region_id: The identifier for the grid region (e.g., "ERCOT")
          
      Returns:
          Carbon intensity in kg CO2/MWh
          
      Raises:
          ValueError: If region_id is not valid
      """
  ```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_mcp_tools.py

# Run with verbose output
pytest -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use pytest fixtures for common setup
- Aim for high coverage on critical paths

Example test:
```python
import pytest
from app.mcp.server import mcp_server

@pytest.mark.asyncio
async def test_get_grid_carbon():
    result = await mcp_server.call_tool("get_grid_carbon", {"region_id": "ERCOT"})
    assert result["success"] is True
    assert "carbon_intensity_kg_per_mwh" in result["result"]
```

## Documentation

- Update README.md for user-facing changes
- Add inline comments for complex logic
- Update API documentation for new endpoints
- Include examples for new features

## Questions?

Feel free to open an issue for any questions about contributing. We're happy to help!

---

Thank you for contributing to MCP Energy Hub! 🌱⚡
