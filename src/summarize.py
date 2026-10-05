"""Stage 4: Template-based buy case generation."""

from .models import Stock, load_stocks, save_stocks
from .config import DATA_DIR, RESEARCH_NOTES


def generate_bull_case(s: Stock) -> list[str]:
    note = RESEARCH_NOTES.get(s.ticker, {})
    if note.get("thesis"):
        return [note["thesis"]]
    points = []
    buyers = [item["investor"] for item in s.investor_activity if item["activity"].startswith(("Buy", "Add"))]
    if buyers:
        points.append(f"Latest reported buys/adds: {', '.join(buyers[:3])}")
    if s.roe and s.roe > 15:
        points.append(f"Strong returns on equity ({s.roe:.1f}%)")
    if s.revenue_growth and s.revenue_growth > 15:
        points.append(f"Solid revenue growth ({s.revenue_growth:.1f}%)")
    if s.fcf_yield and s.fcf_yield > 5:
        points.append(f"High free cash flow yield ({s.fcf_yield:.1f}%)")
    if s.gross_margin and s.gross_margin > 50:
        points.append(f"Wide gross margins ({s.gross_margin:.1f}%)")
    if s.superinvestor_holders:
        names = ", ".join(s.superinvestor_holders[:3])
        points.append(f"Held by: {names}")
    if s.pct_from_52w_high and s.pct_from_52w_high < -15:
        points.append(f"Down {s.pct_from_52w_high:.0f}% from highs; fair value not established")
    if s.pe and s.pe < 15:
        points.append(f"Cheap on earnings (P/E {s.pe:.1f})")
    if not points:
        points.append("No specific business thesis established by this screen")
    return points[:5]


def generate_bear_case(s: Stock) -> list[str]:
    note = RESEARCH_NOTES.get(s.ticker, {})
    if note.get("risk"):
        return [note["risk"], note["gate"], *s.data_notes]
    if note.get("reason"):
        return [note["reason"], *s.data_notes]
    risks = []
    risks.extend(s.data_notes)
    reducers = [item["investor"] for item in s.investor_activity if item["activity"].startswith("Reduce")]
    if reducers:
        risks.append(f"Latest reported trims: {', '.join(reducers[:3])}")
    if s.fcf_yield is not None and s.fcf_yield < 0:
        risks.append(f"Negative free cash flow yield ({s.fcf_yield:.1f}%)")
    if s.debt_equity and s.debt_equity > 1:
        risks.append(f"Elevated debt (D/E {s.debt_equity:.2f})")
    if s.pe and s.pe > 20:
        risks.append(f"Not cheap (P/E {s.pe:.1f})")
    if s.short_float and s.short_float > 10:
        risks.append(f"High short interest ({s.short_float:.1f}%) — market skepticism")
    if s.net_margin and s.net_margin < 5:
        risks.append(f"Thin margins ({s.net_margin:.1f}%)")
    if not risks:
        risks.append("Screen does not assess moat durability, normalized earnings or fair value")
    return risks[:3]


def assign_verdict(s: Stock) -> str:
    if s.timing_label == "no data":
        return "Pass"
    if s.ticker in RESEARCH_NOTES:
        return RESEARCH_NOTES[s.ticker]["tier"]
    # A screen can surface a watch, not establish a buy recommendation.
    if s.smart_money_score > 0 or (s.fcf_yield is not None and s.fcf_yield > 5) or (s.roe is not None and s.roe > 15):
        return "Watch"
    return "Pass"


def generate_one_liner(s: Stock) -> str:
    parts = [s.name or s.ticker]
    if s.sector:
        parts.append(f"({s.sector})")
    if s.market_cap:
        if s.market_cap >= 1e12:
            parts.append(f"— ${s.market_cap/1e12:.1f}T")
        elif s.market_cap >= 1e9:
            parts.append(f"— ${s.market_cap/1e9:.1f}B")
        else:
            parts.append(f"— ${s.market_cap/1e6:.0f}M")
    return " ".join(parts)


def summarize_stocks(stocks: list[Stock]) -> list[Stock]:
    for s in stocks:
        s.bull_case = generate_bull_case(s)
        s.bear_case = generate_bear_case(s)
        s.verdict = assign_verdict(s)
        s.one_liner = generate_one_liner(s)
    order = {"Research": 0, "Watch": 1, "Pass": 2}
    priorities = list(RESEARCH_NOTES)
    stocks.sort(key=lambda s: (order.get(s.verdict, 9), priorities.index(s.ticker) if s.ticker in priorities else len(priorities), -s.smart_money_score))
    return stocks


def run():
    print("📝 Stage 4: Generating summaries...")
    stocks = load_stocks(DATA_DIR / "03_sentiment.json")
    stocks = summarize_stocks(stocks)
    verdicts = {}
    for s in stocks:
        verdicts[s.verdict] = verdicts.get(s.verdict, 0) + 1
    print(f"   Verdicts: {verdicts}")
    save_stocks(stocks, DATA_DIR / "04_final.json")
    return stocks


if __name__ == "__main__":
    run()
