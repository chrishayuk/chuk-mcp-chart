"""Chart MCP Server — interactive data visualisation.

Provides a simple show_chart tool that renders programming language popularity
as a bar, pie, or line chart.

Built with chuk-mcp-server; renders via the chuk-view-schemas chart view.
"""

import logging
import sys

import httpx

from chuk_mcp_server import ChukMCPServer
from chuk_view_schemas.chart import ChartContent, ChartDataset

# ---------------------------------------------------------------------------
# Logging — quiet in STDIO mode to keep the JSON-RPC stream clean
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s:%(name)s:%(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------
mcp = ChukMCPServer(
    name="chuk-mcp-chart",
    version="1.0.0",
    title="Chart Server",
    description="Interactive data visualisation — bar, pie, line, doughnut, radar, polar, and area charts.",
)


VIEW_URL = "https://chuk-mcp-ui-views.fly.dev/chart/v1"
RESOURCE_URI = "ui://chuk-mcp-chart/chart"

# ---------------------------------------------------------------------------
# Resource — serve the chart view HTML so Claude.ai can load it inline
# ---------------------------------------------------------------------------
@mcp.resource(
    uri=RESOURCE_URI,
    name="chart",
    description="Chart view HTML",
    mime_type="text/html;profile=mcp-app",
)
async def chart_view_resource() -> str:
    """Fetch and return the chart view HTML from the CDN."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(VIEW_URL, follow_redirects=True)
        resp.raise_for_status()
        return resp.text


# ---------------------------------------------------------------------------
# Tools — meta format matches FastMCP demo (ui:// resourceUri + viewUrl)
# ---------------------------------------------------------------------------
@mcp.tool(
    name="show_chart",
    description="Show programming language popularity as a chart. chart_type: bar, pie, or line.",
    read_only_hint=True,
    meta={
        "ui": {
            "resourceUri": RESOURCE_URI,
            "viewUrl": VIEW_URL,
        }
    },
)
async def show_chart(chart_type: str = "bar") -> dict:
    """Show programming language popularity as a chart."""
    content = ChartContent(
        title="Programming Language Popularity 2025",
        chart_type=chart_type,
        data=[
            ChartDataset(
                label="Popularity (%)",
                values=[
                    {"label": "Python", "value": 28.1},
                    {"label": "JavaScript", "value": 21.3},
                    {"label": "TypeScript", "value": 12.7},
                    {"label": "Java", "value": 10.5},
                    {"label": "C#", "value": 7.8},
                    {"label": "Go", "value": 5.2},
                    {"label": "Rust", "value": 3.9},
                ],
            )
        ],
    )
    structured = content.model_dump(by_alias=True)
    return {
        "content": [{"type": "text", "text": f"Programming language popularity ({chart_type} chart)."}],
        "structuredContent": structured,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    """Run the Chart MCP server."""
    use_stdio = True

    if len(sys.argv) > 1 and sys.argv[1] in ("http", "--http"):
        use_stdio = False
        logger.warning("Starting Chuk MCP Chart Server in HTTP mode")

    if use_stdio:
        logging.getLogger("chuk_mcp_server").setLevel(logging.ERROR)
        logging.getLogger("chuk_mcp_server.core").setLevel(logging.ERROR)
        logging.getLogger("chuk_mcp_server.stdio_transport").setLevel(logging.ERROR)

    mcp.run(stdio=use_stdio)


if __name__ == "__main__":
    main()
