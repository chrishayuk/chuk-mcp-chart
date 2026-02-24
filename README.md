# Chuk MCP Chart

**Interactive data visualisation via MCP** — paste a CSV, describe your data, ask for a chart. Bar, pie, line, doughnut, radar, polar, and area charts rendered instantly.

> This is a demonstration project provided as-is for learning and testing purposes.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Features

Three tools that turn raw data into beautiful charts:

### 1. Show Chart (`show_chart`)

Create a chart from explicit data. Provide labels, one or more datasets, and optional configuration:

- **Chart types**: bar, line, pie, doughnut, radar, polar, area
- Axis labels, legend position, stacked mode
- Custom colours per dataset
- Auto-assigned colour-blind-friendly palette

### 2. Chart from CSV (`chart_from_csv`)

Paste raw CSV text and get a chart — zero configuration required:

- First non-numeric column becomes category labels
- Every numeric column becomes a dataset (series)
- If all columns are numeric, row numbers are used as labels
- Perfect for spreadsheet data

### 3. Chart from JSON (`chart_from_json`)

Pass a JSON array of objects and get a chart automatically:

- First string field becomes category labels
- Every numeric field becomes a dataset
- Great for API responses or structured data

## Installation

### Using uvx (Recommended - No Installation Required!)

```bash
uvx chuk-mcp-chart
```

This automatically downloads and runs the latest version. Perfect for Claude Desktop!

### Using uv (Recommended for Development)

```bash
# Install from PyPI
uv pip install chuk-mcp-chart

# Or clone and install from source
git clone https://github.com/IBM/chuk-mcp-chart.git
cd chuk-mcp-chart
uv sync --dev
```

### Using pip (Traditional)

```bash
pip install chuk-mcp-chart
```

## Usage

### With Claude Desktop

#### Option 1: Run Locally with uvx

```json
{
  "mcpServers": {
    "chart": {
      "command": "uvx",
      "args": ["chuk-mcp-chart"]
    }
  }
}
```

#### Option 2: Run Locally with pip

```json
{
  "mcpServers": {
    "chart": {
      "command": "chuk-mcp-chart"
    }
  }
}
```

### Standalone

```bash
# With uvx (recommended - always latest version)
uvx chuk-mcp-chart

# With uvx in HTTP mode
uvx chuk-mcp-chart http

# Or if installed locally
chuk-mcp-chart
chuk-mcp-chart http
```

Or with uv/Python:

```bash
# STDIO mode (default, for MCP clients)
uv run chuk-mcp-chart
# or: python -m chuk_mcp_chart.server

# HTTP mode (for web access)
uv run chuk-mcp-chart http
# or: python -m chuk_mcp_chart.server http
```

**STDIO mode** is for MCP clients like Claude Desktop and mcp-cli.
**HTTP mode** runs a web server on http://localhost:8000 for HTTP-based MCP clients.

## Example Prompts

Once configured, try asking:

- "Chart my monthly expenses" (then paste your data)
- "Show Python vs JavaScript popularity as a pie chart"
- "Turn this CSV into a line chart showing trends over time"
- "Create a bar chart of Q1-Q4 revenue: 42000, 51000, 48000, 55000"
- "Show a radar chart comparing three products across speed, quality, and price"
- "Make a doughnut chart of browser market share"

## Tool Reference

### show_chart

Create a chart from explicit labels and datasets.

Parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chart_type` | string | `"bar"` | One of: bar, line, pie, doughnut, radar, polar, area |
| `title` | string | `"Chart"` | Chart title |
| `labels` | string | — | Comma-separated category labels (e.g. `"Jan,Feb,Mar"`) |
| `datasets` | string | — | JSON array of dataset objects (see below) |
| `x_axis_label` | string | — | X axis label |
| `y_axis_label` | string | — | Y axis label |
| `legend_position` | string | — | Legend position: top, bottom, left, right, none |
| `stacked` | bool | `false` | Stack bar/area datasets |

**Dataset format** (JSON string):

```json
[
  {"label": "Revenue", "values": [12, 19, 3, 5, 2, 3]},
  {"label": "Expenses", "values": [8, 14, 2, 4, 1, 2], "color": "#ef4444"}
]
```

### chart_from_csv

Parse CSV text into a chart automatically.

Parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `csv_data` | string | — | Raw CSV text with header row |
| `chart_type` | string | `"bar"` | Chart type |
| `title` | string | `"Chart"` | Chart title |

**Example input**:

```
Month,Revenue,Expenses
Jan,4200,3800
Feb,5100,4200
Mar,4800,4100
```

### chart_from_json

Parse a JSON array into a chart automatically.

Parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `json_data` | string | — | JSON array of objects |
| `chart_type` | string | `"bar"` | Chart type |
| `title` | string | `"Chart"` | Chart title |

**Example input**:

```json
[
  {"language": "Python", "popularity": 28.1},
  {"language": "JavaScript", "popularity": 21.3},
  {"language": "TypeScript", "popularity": 12.7}
]
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/IBM/chuk-mcp-chart.git
cd chuk-mcp-chart

# Install with uv (recommended)
uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

### Running Tests

```bash
make test              # Run tests
make test-cov          # Run tests with coverage
make coverage-report   # Show coverage report
```

### Code Quality

```bash
make lint      # Run linters
make format    # Auto-format code
make typecheck # Run type checking
make security  # Run security checks
make check     # Run all checks
```

### Building

```bash
make build         # Build package
make docker-build  # Build Docker image
```

## Deployment

### Fly.io

Deploy to Fly.io with a single command:

```bash
# First time setup
fly launch

# Deploy updates
fly deploy
```

The server will be available via HTTP at your Fly.io URL.

### Docker

```bash
# Build the image
docker build -t chuk-mcp-chart .

# Run the container
docker run -p 8000:8000 chuk-mcp-chart
```

## Architecture

Built on top of chuk-mcp-server with chart rendering via chuk-view-schemas:

- **Decorator-driven**: Tools defined with `@chart_tool` — handles view metadata, structured content, and text fallback automatically
- **Type-safe**: All chart data uses Pydantic v2 models (`ChartContent`, `ChartDataset`, `AxisConfig`, `LegendConfig`)
- **Smart parsing**: CSV and JSON tools auto-detect labels vs data columns
- **Async native**: All tools are async for optimal performance
- **Dual transport**: STDIO for MCP clients, HTTP for web access

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Apache License 2.0 - See [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Chart.js](https://www.chartjs.org/) for the chart rendering engine
- [chuk-mcp-server](https://github.com/IBM/chuk-mcp-server) for the MCP framework
- [Model Context Protocol](https://modelcontextprotocol.io/) for the MCP specification
- [Anthropic](https://www.anthropic.com/) for Claude and MCP support
