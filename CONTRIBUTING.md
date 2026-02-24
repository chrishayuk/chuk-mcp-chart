# Contributing to chuk-mcp-chart

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- UV (recommended) or pip

### Getting Started

1. **Fork and Clone**

```bash
git clone https://github.com/IBM/chuk-mcp-chart.git
cd chuk-mcp-chart
```

2. **Install Dependencies**

Using UV (recommended):
```bash
uv sync --dev
```

Using pip:
```bash
pip install -e ".[dev]"
```

3. **Verify Installation**

```bash
make test
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

Follow these guidelines:

- Write clear, descriptive commit messages
- Add tests for new functionality
- Update documentation as needed
- Follow the existing code style

### 3. Test Your Changes

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run linting
make lint

# Run all checks
make check
```

### 4. Format Code

```bash
make format
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add awesome new feature"
```

Use conventional commit messages:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style

We use Ruff for linting and formatting:

- Line length: 100 characters
- Type hints required for public APIs
- Docstrings for all public functions and classes
- Follow PEP 8 conventions

## Adding New Chart Types

Chart tools are defined in `src/chuk_mcp_chart/server.py` using the `@chart_tool` decorator. When adding a new chart type or tool:

1. **Add the tool function** in `server.py` decorated with `@chart_tool`
2. **Add helpers** in `helpers.py` if parsing logic is needed
3. **Add documentation** in `README.md`
4. **Add tests** in `tests/`

## Project Structure

```
chuk-mcp-chart/
├── src/
│   └── chuk_mcp_chart/
│       ├── __init__.py
│       ├── server.py       # MCP tool definitions
│       └── helpers.py      # CSV/JSON parsing utilities
├── tests/                  # Test files
├── pyproject.toml          # Project configuration
├── Makefile                # Development commands
├── Dockerfile              # Docker configuration
└── README.md               # Main documentation
```

## Getting Help

- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions or share ideas
- **Pull Requests**: Contribute code or documentation

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help others learn and grow

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes
- Project documentation

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
