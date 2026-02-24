"""Chart MCP Server — interactive data visualisation.

Provides three tools for creating charts:
- show_chart: Build a chart from explicit labels, datasets, and options.
- chart_from_csv: Parse raw CSV text and produce a chart automatically.
- chart_from_json: Parse a JSON array and produce a chart automatically.

Supported chart types: bar, line, pie, doughnut, radar, polar, area.

Built with chuk-mcp-server; renders via the chuk-view-schemas chart view.
"""

import json
import logging
import sys
from typing import Optional

from chuk_mcp_server import ChukMCPServer
from chuk_view_schemas.chart import ChartContent, AxisConfig, ChartDataset, LegendConfig
from chuk_view_schemas.chuk_mcp import chart_tool

from .helpers import (
    assign_colours,
    build_values,
    csv_to_chart_content,
    json_to_chart_content,
    normalise_dataset,
    parse_csv,
    parse_datasets,
    parse_labels,
    resolve_chart_type,
)

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


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@chart_tool(
    mcp,
    "show_chart",
    description=(
        "Advanced chart tool with full control over axes, legend, and stacking. "
        "Prefer chart_from_json for simple charts — use this only when you need "
        "axis labels, legend position, stacking, or multiple overlaid datasets. "
        "labels: comma-separated (e.g. 'Jan,Feb,Mar'). "
        'datasets: JSON array of {"label":"Name","values":[1,2,3]}.'
    ),
    read_only_hint=True,
)
async def show_chart(
    chart_type: str = "bar",
    title: str = "Chart",
    labels: Optional[str] = None,
    datasets: Optional[str] = None,
    x_axis_label: Optional[str] = None,
    y_axis_label: Optional[str] = None,
    legend_position: Optional[str] = None,
    stacked: bool = False,
) -> ChartContent:
    """Create an interactive chart from explicit data.

    Args:
        chart_type: Chart type — one of: bar, line, pie, doughnut, radar, polar, area.
        title: Chart title displayed above the chart.
        labels: Comma-separated category labels for the X axis or pie segments.
            Example: "Jan,Feb,Mar,Apr,May"
        datasets: JSON string — an array of dataset objects. Each object must have:
            - "label" (str): Legend name for the series.
            - "values" (list[float]): Numeric values (one per label).
            Optional keys: "color", "backgroundColor", "fill", "tension".
            Example: '[{"label":"Sales","values":[10,20,30]},{"label":"Returns","values":[2,4,1]}]'
        x_axis_label: Label for the X axis.
        y_axis_label: Label for the Y axis.
        legend_position: Position of the legend — top, bottom, left, right, none.
        stacked: If true, stack bar / area datasets.

    Returns:
        ChartContent rendered in the chart view.

    Example usage by an LLM:
        "Show my monthly sales as a bar chart"
        → show_chart(chart_type="bar", title="Monthly Sales",
                      labels="Jan,Feb,Mar,Apr,May,Jun",
                      datasets='[{"label":"Revenue","values":[12,19,3,5,2,3]}]')

        "Compare Python vs JavaScript popularity as a pie chart"
        → show_chart(chart_type="pie", title="Language Popularity",
                      labels="Python,JavaScript,TypeScript,Java,Go",
                      datasets='[{"label":"Popularity %","values":[28.1,21.3,12.7,10.5,5.2]}]')
    """
    ct = resolve_chart_type(chart_type)

    # Parse labels — handles both comma-separated and JSON array strings
    parsed_labels: list[str] = parse_labels(labels) if labels else []

    # Parse datasets — tolerant of LLM variations
    parsed_datasets = parse_datasets(datasets)

    # Normalise and build values for each dataset
    built_datasets: list[dict] = []
    for ds in parsed_datasets:
        ds = normalise_dataset(ds)
        ds["values"] = build_values(ds.get("values", []), parsed_labels)
        built_datasets.append(ds)

    built_datasets = assign_colours(built_datasets)

    # Axis config
    x_axis = (
        AxisConfig(label=x_axis_label, stacked=stacked or None) if x_axis_label or stacked else None
    )
    y_axis = (
        AxisConfig(label=y_axis_label, stacked=stacked or None) if y_axis_label or stacked else None
    )

    # Legend
    legend = LegendConfig(position=legend_position) if legend_position else None

    return ChartContent(
        title=title,
        chart_type=ct,
        data=[ChartDataset(**ds) for ds in built_datasets],
        x_axis=x_axis,
        y_axis=y_axis,
        legend=legend,
    )


@chart_tool(
    mcp,
    "chart_from_csv",
    description=(
        "Create a chart from CSV text. Best when the user pastes or provides CSV data. "
        "The first non-numeric column becomes labels; numeric columns become datasets. "
        'Example csv_data: "Name,Score\\nAlice,85\\nBob,92\\nCarol,78"'
    ),
    read_only_hint=True,
)
async def chart_from_csv(
    csv_data: str,
    chart_type: str = "bar",
    title: Optional[str] = None,
) -> ChartContent:
    """Create a chart by parsing CSV text.

    The CSV is auto-analysed:
    - The first non-numeric column is used for category labels.
    - Every numeric column becomes a separate dataset (series).
    - If all columns are numeric, row numbers are used as labels.

    Args:
        csv_data: Raw CSV text with a header row. Example:
            "Month,Sales,Returns\\nJan,120,5\\nFeb,150,8\\nMar,130,3"
        chart_type: Chart type — bar, line, pie, doughnut, radar, polar, area.
        title: Optional chart title. Defaults to "Chart".

    Returns:
        ChartContent rendered in the chart view.

    Example usage by an LLM:
        User pastes:
            Month,Revenue,Expenses
            Jan,4200,3800
            Feb,5100,4200
            Mar,4800,4100

        → chart_from_csv(csv_data="Month,Revenue,Expenses\\nJan,4200,3800\\nFeb,5100,4200\\nMar,4800,4100",
                          chart_type="line", title="Revenue vs Expenses")
    """
    header, data_rows = parse_csv(csv_data)
    return csv_to_chart_content(header, data_rows, chart_type, title)


@chart_tool(
    mcp,
    "chart_from_json",
    description=(
        "RECOMMENDED — the easiest way to create a chart. Pass a JSON array of objects; "
        "the first string field becomes labels, every numeric field becomes a dataset. "
        'Example: [{"name":"Python","score":28},{"name":"JS","score":21}]. '
        "chart_type: bar, line, pie, doughnut, radar, polar, or area."
    ),
    read_only_hint=True,
)
async def chart_from_json(
    json_data: str,
    chart_type: str = "bar",
    title: Optional[str] = None,
) -> ChartContent:
    """Create a chart by parsing a JSON array.

    The JSON is auto-analysed:
    - The first string field in each object is used for category labels.
    - Every numeric field becomes a separate dataset (series).

    Args:
        json_data: A JSON string containing an array of objects. Example:
            '[{"language":"Python","pct":28.1},{"language":"JavaScript","pct":21.3}]'
        chart_type: Chart type — bar, line, pie, doughnut, radar, polar, area.
        title: Optional chart title. Defaults to "Chart".

    Returns:
        ChartContent rendered in the chart view.

    Example usage by an LLM:
        User asks "Chart the top 5 programming languages":
        → chart_from_json(
              json_data='[{"language":"Python","popularity":28.1},{"language":"JavaScript","popularity":21.3},{"language":"TypeScript","popularity":12.7},{"language":"Java","popularity":10.5},{"language":"Go","popularity":5.2}]',
              chart_type="pie",
              title="Top 5 Programming Languages 2025")
    """
    try:
        data = json.loads(json_data)
    except json.JSONDecodeError as exc:
        raise ValueError(f"json_data must be a valid JSON array: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("json_data must be a JSON array of objects.")

    if not data or not isinstance(data[0], dict):
        raise ValueError("json_data must be a non-empty array of objects.")

    return json_to_chart_content(data, chart_type, title)


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
