"""BudgetWise tests - no LLM and no network needed. Run with:  python -m pytest

Part 1 calls the tool functions directly; part 2 starts the real MCP server and calls them through MCP."""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mcp_server as tools  # noqa: E402


def test_spending_by_category_top_discretionary_is_dining():
    r = tools.get_spending_by_category(30)
    assert r["top_category"] == "rent"
    assert r["top_discretionary_category"] == "dining"
    dining = next(c for c in r["by_category"] if c["category"] == "dining")
    assert dining["total"] == 359.10
    assert r["total_spent"] == 2485.70


def test_spending_rejects_bad_input():
    assert "error" in tools.get_spending_by_category(0)
    assert "error" in tools.get_spending_by_category(9999)


def test_safe_to_spend():
    r = tools.get_safe_to_spend()
    assert r["days_until_paycheck"] == 11
    assert r["bills_total"] == 1245.00  # internet (due after payday) is excluded
    assert r["safe_to_spend_total"] == 430.25
    assert r["safe_to_spend_per_day"] == 39.11
    assert r["warning"] is None


def test_income_variability():
    r = tools.get_income_variability(3)
    assert [m["income"] for m in r["per_month"]] == [2850.00, 3420.00, 2610.00]
    assert r["average_income"] == 2960.00
    assert r["lowest_month_income"] == 2610.00
    assert r["highest_month_income"] == 3420.00
    assert r["conservative_baseline"] == 2610.00


def test_income_rejects_bad_input():
    assert "error" in tools.get_income_variability(0)


# ---- Part 2: through the real MCP protocol ----
SERVER = Path(__file__).resolve().parent.parent / "mcp_server.py"


async def _call(tool: str, args: dict | None = None):
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = [t.name for t in (await session.list_tools()).tools]
            res = await session.call_tool(tool, args or {})
            return listed, json.loads(res.content[0].text)


def test_server_lists_three_tools():
    listed, _ = asyncio.run(_call("get_safe_to_spend"))
    assert sorted(listed) == ["get_income_variability", "get_safe_to_spend", "get_spending_by_category"]


def test_mcp_safe_to_spend_executes():
    _, data = asyncio.run(_call("get_safe_to_spend"))
    assert data["safe_to_spend_per_day"] == 39.11


def test_mcp_spending_executes():
    _, data = asyncio.run(_call("get_spending_by_category", {"days": 30}))
    assert data["top_discretionary_category"] == "dining"


def test_mcp_income_executes():
    _, data = asyncio.run(_call("get_income_variability", {"months": 3}))
    assert data["conservative_baseline"] == 2610.00
