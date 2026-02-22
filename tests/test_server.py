"""Tests for chuk-mcp-chart server."""

import json

import pytest

from chuk_mcp_chart.server import show_chart, chart_from_csv, chart_from_json


# ---------------------------------------------------------------------------
# show_chart
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_show_chart_bar_basic():
    result = await show_chart(
        chart_type="bar",
        title="Test Bar",
        labels="A,B,C",
        datasets='[{"label":"Series 1","values":[10,20,30]}]',
    )
    assert result.title == "Test Bar"
    assert result.chart_type == "bar"
    assert len(result.data) == 1
    assert len(result.data[0].values) == 3


@pytest.mark.asyncio
async def test_show_chart_pie():
    result = await show_chart(
        chart_type="pie",
        title="Pie Chart",
        labels="Python,JS,Go",
        datasets='[{"label":"Popularity","values":[28,21,5]}]',
    )
    assert result.chart_type == "pie"
    assert len(result.data[0].values) == 3


@pytest.mark.asyncio
async def test_show_chart_line_with_axes():
    result = await show_chart(
        chart_type="line",
        title="Sales",
        labels="Jan,Feb,Mar",
        datasets='[{"label":"Revenue","values":[100,200,150]}]',
        x_axis_label="Month",
        y_axis_label="$USD",
    )
    assert result.chart_type == "line"
    assert result.x_axis is not None
    assert result.x_axis.label == "Month"
    assert result.y_axis.label == "$USD"


@pytest.mark.asyncio
async def test_show_chart_stacked():
    result = await show_chart(
        chart_type="bar",
        title="Stacked",
        labels="A,B",
        datasets='[{"label":"X","values":[1,2]},{"label":"Y","values":[3,4]}]',
        stacked=True,
    )
    assert result.x_axis.stacked is True
    assert result.y_axis.stacked is True


@pytest.mark.asyncio
async def test_show_chart_legend():
    result = await show_chart(
        chart_type="bar",
        title="Legend",
        labels="A,B",
        datasets='[{"label":"X","values":[1,2]}]',
        legend_position="bottom",
    )
    assert result.legend is not None
    assert result.legend.position == "bottom"


@pytest.mark.asyncio
async def test_show_chart_doughnut():
    result = await show_chart(
        chart_type="doughnut",
        labels="A,B,C",
        datasets='[{"label":"Data","values":[10,20,30]}]',
    )
    assert result.chart_type == "doughnut"


@pytest.mark.asyncio
async def test_show_chart_radar():
    result = await show_chart(
        chart_type="radar",
        labels="Speed,Power,Range",
        datasets='[{"label":"Model A","values":[8,6,7]}]',
    )
    assert result.chart_type == "radar"


@pytest.mark.asyncio
async def test_show_chart_area():
    result = await show_chart(
        chart_type="area",
        labels="Q1,Q2,Q3,Q4",
        datasets='[{"label":"Growth","values":[10,25,40,55]}]',
    )
    assert result.chart_type == "area"


@pytest.mark.asyncio
async def test_show_chart_no_labels():
    result = await show_chart(
        chart_type="bar",
        datasets='[{"label":"Data","values":[5,10,15]}]',
    )
    assert len(result.data[0].values) == 3


@pytest.mark.asyncio
async def test_show_chart_no_datasets():
    result = await show_chart(chart_type="bar", labels="A,B,C")
    assert len(result.data) == 1
    assert result.data[0].label == "Data"


@pytest.mark.asyncio
async def test_show_chart_invalid_json_raises():
    with pytest.raises(ValueError, match="valid JSON"):
        await show_chart(datasets="not json")


@pytest.mark.asyncio
async def test_show_chart_single_dataset_object_wrapped():
    """LLMs sometimes send a single object instead of an array — should auto-wrap."""
    result = await show_chart(
        labels="A,B",
        datasets='{"label":"X","values":[1,2]}',
    )
    assert len(result.data) == 1
    assert result.data[0].label == "X"


@pytest.mark.asyncio
async def test_show_chart_datasets_not_array_raises():
    with pytest.raises(ValueError, match="JSON array"):
        await show_chart(datasets='"just a string"')


@pytest.mark.asyncio
async def test_show_chart_multiple_datasets():
    result = await show_chart(
        chart_type="line",
        labels="Jan,Feb,Mar",
        datasets='[{"label":"A","values":[1,2,3]},{"label":"B","values":[4,5,6]}]',
    )
    assert len(result.data) == 2
    assert result.data[0].color is not None
    assert result.data[1].color is not None
    assert result.data[0].color != result.data[1].color


# ---------------------------------------------------------------------------
# chart_from_csv
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_csv_basic():
    csv_text = "Month,Sales\nJan,100\nFeb,200\nMar,150"
    result = await chart_from_csv(csv_data=csv_text, chart_type="bar", title="Sales")
    assert result.title == "Sales"
    assert result.chart_type == "bar"
    assert len(result.data) == 1
    assert result.data[0].label == "Sales"
    assert len(result.data[0].values) == 3


@pytest.mark.asyncio
async def test_csv_multiple_numeric_columns():
    csv_text = "Month,Revenue,Expenses\nJan,4200,3800\nFeb,5100,4200"
    result = await chart_from_csv(csv_data=csv_text, chart_type="line")
    assert len(result.data) == 2
    assert result.data[0].label == "Revenue"
    assert result.data[1].label == "Expenses"


@pytest.mark.asyncio
async def test_csv_all_numeric():
    csv_text = "A,B\n1,10\n2,20\n3,30"
    result = await chart_from_csv(csv_data=csv_text)
    # All columns numeric → row indices as labels
    assert len(result.data) == 2


@pytest.mark.asyncio
async def test_csv_pie():
    csv_text = "Language,Pct\nPython,28\nJS,21\nGo,5"
    result = await chart_from_csv(csv_data=csv_text, chart_type="pie", title="Languages")
    assert result.chart_type == "pie"
    assert len(result.data[0].values) == 3


@pytest.mark.asyncio
async def test_csv_too_few_rows_raises():
    with pytest.raises(ValueError, match="at least a header"):
        await chart_from_csv(csv_data="OnlyHeader")


@pytest.mark.asyncio
async def test_csv_no_numeric_raises():
    with pytest.raises(ValueError, match="numeric column"):
        await chart_from_csv(csv_data="Name,City\nAlice,NYC\nBob,LA")


@pytest.mark.asyncio
async def test_csv_default_title():
    csv_text = "X,Y\n1,10\n2,20"
    result = await chart_from_csv(csv_data=csv_text)
    assert result.title == "Chart"


# ---------------------------------------------------------------------------
# chart_from_json
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_json_basic():
    data = [
        {"language": "Python", "pct": 28.1},
        {"language": "JavaScript", "pct": 21.3},
    ]
    result = await chart_from_json(json_data=json.dumps(data), chart_type="pie", title="Lang")
    assert result.title == "Lang"
    assert result.chart_type == "pie"
    assert len(result.data) == 1
    assert result.data[0].label == "pct"
    assert len(result.data[0].values) == 2


@pytest.mark.asyncio
async def test_json_multiple_numeric_fields():
    data = [
        {"month": "Jan", "revenue": 100, "expenses": 80},
        {"month": "Feb", "revenue": 150, "expenses": 120},
    ]
    result = await chart_from_json(json_data=json.dumps(data), chart_type="bar")
    assert len(result.data) == 2


@pytest.mark.asyncio
async def test_json_no_string_field():
    data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    result = await chart_from_json(json_data=json.dumps(data))
    # No string field → index labels
    assert len(result.data) == 2


@pytest.mark.asyncio
async def test_json_invalid_raises():
    with pytest.raises(ValueError, match="valid JSON"):
        await chart_from_json(json_data="not json")


@pytest.mark.asyncio
async def test_json_not_array_raises():
    with pytest.raises(ValueError, match="JSON array"):
        await chart_from_json(json_data='{"key":"val"}')


@pytest.mark.asyncio
async def test_json_empty_array_raises():
    with pytest.raises(ValueError, match="non-empty"):
        await chart_from_json(json_data="[]")


@pytest.mark.asyncio
async def test_json_no_numeric_raises():
    with pytest.raises(ValueError, match="numeric field"):
        await chart_from_json(json_data='[{"name":"Alice","city":"NYC"}]')


@pytest.mark.asyncio
async def test_json_default_title():
    data = [{"x": 1}, {"x": 2}]
    result = await chart_from_json(json_data=json.dumps(data))
    assert result.title == "Chart"


# ---------------------------------------------------------------------------
# Colour assignment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_colours_assigned():
    result = await show_chart(
        labels="A,B",
        datasets='[{"label":"X","values":[1,2]},{"label":"Y","values":[3,4]},{"label":"Z","values":[5,6]}]',
    )
    colours = [ds.color for ds in result.data]
    assert all(c is not None for c in colours)
    # All different
    assert len(set(colours)) == 3


@pytest.mark.asyncio
async def test_custom_colour_preserved():
    result = await show_chart(
        labels="A",
        datasets='[{"label":"X","values":[1],"color":"#ff0000"}]',
    )
    assert result.data[0].color == "#ff0000"


# ---------------------------------------------------------------------------
# Chart type aliases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_polar_alias():
    result = await show_chart(
        chart_type="polar",
        labels="A,B,C",
        datasets='[{"label":"Data","values":[1,2,3]}]',
    )
    assert result.chart_type == "radar"


# ---------------------------------------------------------------------------
# main() entry point
# ---------------------------------------------------------------------------


def test_main_function_exists():
    from chuk_mcp_chart.server import main

    assert callable(main)


def test_imports():
    from chuk_mcp_chart import server

    assert hasattr(server, "show_chart")
    assert hasattr(server, "chart_from_csv")
    assert hasattr(server, "chart_from_json")


# ---------------------------------------------------------------------------
# LLM robustness — handle common variations in how LLMs call the tools
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_labels_as_json_array_string():
    """LLMs sometimes send labels as a JSON array instead of comma-separated."""
    result = await show_chart(
        labels='["Camembert","Brie","Roquefort"]',
        datasets='[{"label":"Score","values":[95,90,88]}]',
    )
    vals = result.data[0].values
    assert vals[0]["label"] == "Camembert"
    assert vals[1]["label"] == "Brie"
    assert vals[2]["label"] == "Roquefort"


@pytest.mark.asyncio
async def test_dataset_data_key_alias():
    """LLMs often use 'data' instead of 'values' (Chart.js convention)."""
    result = await show_chart(
        labels="A,B,C",
        datasets='[{"label":"Series","data":[10,20,30]}]',
    )
    assert len(result.data[0].values) == 3


@pytest.mark.asyncio
async def test_dataset_backgroundColor_alias():
    """LLMs use 'backgroundColor' (Chart.js) instead of 'color'."""
    result = await show_chart(
        labels="A,B",
        datasets='[{"label":"X","values":[1,2],"backgroundColor":"#3b82f6"}]',
    )
    assert result.data[0].color == "#3b82f6"


@pytest.mark.asyncio
async def test_pre_structured_labeled_values_passthrough():
    """LLMs sometimes pre-structure values as LabeledValue objects."""
    result = await show_chart(
        datasets='[{"label":"Score","values":[{"label":"Camembert","value":95},{"label":"Brie","value":90}]}]',
    )
    vals = result.data[0].values
    assert vals[0]["label"] == "Camembert"
    assert vals[0]["value"] == 95
    assert vals[1]["label"] == "Brie"


@pytest.mark.asyncio
async def test_pre_structured_values_with_labels_ignored():
    """When values are already LabeledValue dicts, extra labels param is harmless."""
    result = await show_chart(
        labels="X,Y",
        datasets='[{"label":"Data","values":[{"label":"A","value":10},{"label":"B","value":20}]}]',
    )
    vals = result.data[0].values
    # Pre-structured values should pass through as-is
    assert vals[0]["label"] == "A"
    assert vals[1]["label"] == "B"


@pytest.mark.asyncio
async def test_dataset_data_and_backgroundColor_combined():
    """Real LLM output: uses 'data' + 'backgroundColor' together."""
    result = await show_chart(
        labels='["A","B","C"]',
        datasets='[{"label":"Pop","data":[95,90,88],"backgroundColor":"#3b82f6"}]',
    )
    assert len(result.data[0].values) == 3
    assert result.data[0].color == "#3b82f6"
    vals = result.data[0].values
    assert vals[0]["label"] == "A"
    assert vals[0]["value"] == 95
