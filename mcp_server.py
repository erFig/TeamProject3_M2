"""BudgetWise MCP server (stdio): the three finance tools the agent can call.

All money math lives here, not in the LLM. Data comes from the FAKE sample files in data/.
The agent (agent.py) launches this file automatically. To run it alone: python mcp_server.py
NOTE: never print() in this file - stdout is the MCP protocol channel.
"""
import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("BudgetWise Tools", log_level="WARNING")  # keep the console quiet

DATA_DIR = Path(__file__).resolve().parent / "data"
# Fixed costs the user cannot easily cut; used to find the top *discretionary* category.
FIXED_CATEGORIES = {"rent", "utilities", "debt_payment"}


def _load_profile() -> dict:
    with open(DATA_DIR / "profile.json", encoding="utf-8") as f:
        return json.load(f)


def _load_transactions() -> list[dict]:
    with open(DATA_DIR / "transactions.csv", newline="", encoding="utf-8") as f:
        return [
            {
                "date": date.fromisoformat(r["date"]),
                "description": r["description"],
                "category": r["category"],
                "amount": float(r["amount"]),
            }
            for r in csv.DictReader(f)
        ]


# --------------------------------------------------------------------------- Tool 1
@mcp.tool()
def get_spending_by_category(days: int = 30) -> dict:
    """Get total spending per category over the last N days (default 30).
    Returns category totals, share of spending, the top category overall, and the
    top discretionary category (excludes rent, utilities, debt payments)."""
    if not isinstance(days, int) or days < 1 or days > 365:
        return {"error": "days must be a whole number between 1 and 365"}
    end = date.fromisoformat(_load_profile()["as_of"])
    start = end - timedelta(days=days)  # window is (start, end]
    totals: dict[str, float] = defaultdict(float)
    for t in _load_transactions():
        if start < t["date"] <= end and t["amount"] < 0:
            totals[t["category"]] += -t["amount"]
    total_spent = sum(totals.values())
    by_category = [
        {
            "category": c,
            "total": round(v, 2),
            "share_pct": round(100 * v / total_spent, 1) if total_spent else 0.0,
        }
        for c, v in sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    ]
    discretionary = [c for c in by_category if c["category"] not in FIXED_CATEGORIES]
    return {
        "window_start_exclusive": start.isoformat(),
        "window_end": end.isoformat(),
        "days": days,
        "total_spent": round(total_spent, 2),
        "by_category": by_category,
        "top_category": by_category[0]["category"] if by_category else None,
        "top_discretionary_category": discretionary[0]["category"] if discretionary else None,
    }


# --------------------------------------------------------------------------- Tool 2
@mcp.tool()
def get_safe_to_spend() -> dict:
    """Calculate how much money is safe to spend before the next paycheck:
    balance minus bills due before payday minus the savings buffer, in total and per day."""
    p = _load_profile()
    as_of = date.fromisoformat(p["as_of"])
    payday = date.fromisoformat(p["next_paycheck_date"])
    days_left = max((payday - as_of).days, 1)
    bills = [
        b for b in p["upcoming_bills"]
        if as_of <= date.fromisoformat(b["due_date"]) <= payday
    ]
    bills_total = round(sum(b["amount"] for b in bills), 2)
    safe = round(p["current_balance"] - bills_total - p["savings_buffer"], 2)
    return {
        "as_of": as_of.isoformat(),
        "next_paycheck_date": payday.isoformat(),
        "days_until_paycheck": days_left,
        "current_balance": p["current_balance"],
        "bills_due_before_paycheck": bills,
        "bills_total": bills_total,
        "savings_buffer": p["savings_buffer"],
        "safe_to_spend_total": safe,
        "safe_to_spend_per_day": round(safe / days_left, 2),
        "warning": "Bills and buffer already exceed your balance." if safe < 0 else None,
    }


# --------------------------------------------------------------------------- Tool 3
@mcp.tool()
def get_income_variability(months: int = 3) -> dict:
    """Summarize how much monthly income varies over the last N complete months
    (default 3): per-month income, average, lowest, highest, and a conservative baseline."""
    if not isinstance(months, int) or months < 1 or months > 12:
        return {"error": "months must be a whole number between 1 and 12"}
    as_of = date.fromisoformat(_load_profile()["as_of"])
    y, m = as_of.year, as_of.month
    wanted = []  # the complete calendar months before the as_of month
    for _ in range(months):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        wanted.append((y, m))
    income: dict[tuple[int, int], float] = defaultdict(float)
    for t in _load_transactions():
        key = (t["date"].year, t["date"].month)
        if key in wanted and t["amount"] > 0:
            income[key] += t["amount"]
    per_month = [
        {"month": f"{y}-{m:02d}", "income": round(income.get((y, m), 0.0), 2)}
        for (y, m) in sorted(wanted)
    ]
    values = [x["income"] for x in per_month]
    lowest, highest = min(values), max(values)
    return {
        "months_analyzed": months,
        "per_month": per_month,
        "average_income": round(sum(values) / len(values), 2),
        "lowest_month_income": lowest,
        "highest_month_income": highest,
        "swing": round(highest - lowest, 2),
        "conservative_baseline": lowest,
        "note": "Plan fixed costs against conservative_baseline (the lowest month).",
    }


if __name__ == "__main__":
    mcp.run()  # stdio transport
