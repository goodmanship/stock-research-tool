"""Generate dossier pages for strong-buy stocks."""

from __future__ import annotations

import re
from pathlib import Path

import yfinance as yf
from jinja2 import Environment, FileSystemLoader

from .config import DATA_DIR, DOCS_DIR, TEMPLATES_DIR
from .models import Stock, load_stocks


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def fmt_money(value: float | None) -> str:
    if value is None:
        return "n/a"
    if value >= 1e12:
        return f"${value/1e12:.1f}T"
    if value >= 1e9:
        return f"${value/1e9:.1f}B"
    if value >= 1e6:
        return f"${value/1e6:.0f}M"
    return f"${value:,.0f}"


def fmt_pct(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}%"


def clean_summary(text: str) -> list[str]:
    if not text:
        return []
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    return parts[:4]


def business_model(info: dict, stock: Stock) -> list[str]:
    lines: list[str] = []
    summary = (info.get("longBusinessSummary") or "").lower()
    industry = stock.industry.lower()

    if "airline" in industry or "air carrier" in summary:
        lines.append("Makes money by selling passenger tickets, cargo capacity, and loyalty-program economics across its route network.")
    elif "healthcare plan" in industry:
        lines.append("Makes money through insurance premiums, pharmacy benefit management fees, and health-services contracts with employers, governments, and members.")
    elif "biotechnology" in industry or "rare diseases" in summary:
        lines.append("Makes money by commercializing specialty drugs, mainly in rare-disease niches with concentrated prescriber bases.")
    else:
        lines.append(f"Makes money within the {stock.industry or stock.sector} value chain, based on the operating profile described by company filings and market data.")

    rev_growth = info.get("revenueGrowth")
    earn_growth = info.get("earningsGrowth")
    if rev_growth is not None and rev_growth > 0.08:
        lines.append(f"Recent growth is being helped by revenue expanding about {rev_growth*100:.1f}% year over year.")
    elif earn_growth is not None and earn_growth > 0.1:
        lines.append(f"Recent momentum appears more earnings-driven, with earnings growth around {earn_growth*100:.1f}%.")
    else:
        lines.append("Growth looks modest or mixed right now, so the case leans more on valuation, margins, or capital allocation than on explosive top-line expansion.")

    gross = info.get("grossMargins")
    roe = info.get("returnOnEquity")
    if gross is not None and gross > 0.6:
        lines.append("Its edge appears to come from a high-margin business model, which usually signals pricing power, IP, or a niche position.")
    elif roe is not None and roe > 0.2:
        lines.append("Its edge appears to be efficient capital deployment, with returns on equity well above average.")
    else:
        lines.append("Its edge is less obvious from the raw numbers alone, so this one deserves a more qualitative look at competitive position and management execution.")

    return lines


def fair_assessment(stock: Stock, info: dict) -> dict:
    positives = []
    cautions = []

    if stock.fcf_yield and stock.fcf_yield > 5:
        positives.append(f"Free cash flow yield is strong at {stock.fcf_yield:.1f}%.")
    if stock.forward_pe and stock.forward_pe < 10:
        positives.append(f"Forward valuation looks inexpensive at about {stock.forward_pe:.1f}x earnings.")
    if stock.superinvestor_holders:
        positives.append("Tracked superinvestor ownership is present, which at least suggests credible outside interest.")
    if stock.pct_from_52w_high and stock.pct_from_52w_high < -15:
        positives.append(f"Shares are down about {abs(stock.pct_from_52w_high):.0f}% from the 52-week high, which may create an entry point if fundamentals hold.")

    if stock.net_margin is not None and stock.net_margin < 5:
        cautions.append(f"Net margin is thin at {stock.net_margin:.1f}%, so execution slips can matter a lot.")
    if stock.debt_equity and stock.debt_equity > 1:
        cautions.append(f"Leverage is elevated with debt/equity around {stock.debt_equity:.2f}.")
    if info.get("earningsGrowth") is not None and info.get("earningsGrowth") < 0:
        cautions.append(f"Earnings growth is currently negative at roughly {info.get('earningsGrowth')*100:.1f}%.")
    if stock.short_float and stock.short_float > 8:
        cautions.append(f"Short interest is notable at {stock.short_float:.1f}% of float, which can mean skepticism is real.")

    if not positives:
        positives.append("The main appeal here is the combined screen result rather than one overwhelming metric.")
    if not cautions:
        cautions.append("No obvious red flag jumps off the page, but this still needs normal diligence on competition, management, and cyclicality.")

    return {"positives": positives[:4], "cautions": cautions[:4]}


def investor_context(stock: Stock) -> list[dict]:
    if not stock.superinvestor_holders:
        return []
    items = []
    for name in stock.superinvestor_holders:
        items.append({
            "name": name,
            "status": "Tracked holder",
            "cost_basis": "Unavailable from current data source",
            "note": "We know this investor currently shows up in the tracked holdings set, but not the exact purchase price from the pipeline's current sources.",
        })
    return items


def build_dossier_payload(stock: Stock) -> dict:
    info = yf.Ticker(stock.ticker).info
    assessment = fair_assessment(stock, info)
    slug = slugify(stock.ticker)

    return {
        "ticker": stock.ticker,
        "slug": slug,
        "name": info.get("longName") or stock.name,
        "website": info.get("website"),
        "sector": stock.sector,
        "industry": stock.industry,
        "hq": ", ".join([x for x in [info.get("city"), info.get("state"), info.get("country")] if x]),
        "employees": info.get("fullTimeEmployees"),
        "market_cap": fmt_money(stock.market_cap or info.get("marketCap")),
        "price": stock.price,
        "forward_pe": stock.forward_pe,
        "pe": stock.pe,
        "roe": fmt_pct(stock.roe),
        "gross_margin": fmt_pct(stock.gross_margin),
        "net_margin": fmt_pct(stock.net_margin),
        "fcf_yield": fmt_pct(stock.fcf_yield),
        "revenue_growth": fmt_pct((info.get("revenueGrowth") or 0) * 100 if info.get("revenueGrowth") is not None else None),
        "earnings_growth": fmt_pct((info.get("earningsGrowth") or 0) * 100 if info.get("earningsGrowth") is not None else None),
        "institutional_pct": fmt_pct(stock.institutional_pct),
        "pct_from_52w_high": fmt_pct(stock.pct_from_52w_high),
        "short_float": fmt_pct(stock.short_float),
        "summary_paragraphs": clean_summary(info.get("longBusinessSummary") or ""),
        "business_model": business_model(info, stock),
        "assessment": assessment,
        "investors": investor_context(stock),
        "verdict": stock.verdict,
        "timing_label": stock.timing_label,
        "one_liner": stock.one_liner,
    }


def build() -> list[Path]:
    stocks = load_stocks(DATA_DIR / "04_final.json")
    strong_buys = [s for s in stocks if s.verdict == "Strong Buy"]

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("dossier.html")
    out_dir = DOCS_DIR / "stocks"
    out_dir.mkdir(exist_ok=True)

    written = []
    for stock in strong_buys:
        payload = build_dossier_payload(stock)
        html = template.render(stock=payload, title=f"{stock.ticker} dossier")
        out = out_dir / f"{payload['slug']}.html"
        out.write_text(html)
        written.append(out)
    return written


def run():
    files = build()
    print(f"   ✅ Built {len(files)} dossier pages")


if __name__ == "__main__":
    run()
