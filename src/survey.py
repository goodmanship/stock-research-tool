"""Stage 2: Smart money cross-reference (Dataroma superinvestor holdings)."""

import httpx
import json
import re
from bs4 import BeautifulSoup
from .models import Stock, load_stocks, save_stocks
from .config import DATA_DIR

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

# Map: search term -> display name, dataroma fund code
# Using fund codes directly is more reliable than name matching
SUPERINVESTORS = {
    "BRK": "Warren Buffett",
    "psc": "Bill Ackman",
    "BAUPOST": "Seth Klarman",
    "AM": "David Tepper",
    "oc": "Howard Marks",
    "HC": "Li Lu",
    "PI": "Mohnish Pabrai",
    "FS": "Terry Smith",
    "AC": "Chuck Akre",
    "MKL": "Tom Gayner",
    # Bonus picks
    "RC": "Ruane Cunniff",
    "GLRE": "David Einhorn",
    "ic": "Carl Icahn",
    "tp": "Daniel Loeb",
    "HH": "Duan Yongping",
    "PC": "Norbert Lou",
    "GA": "Greenhaven Associates",
}

PREFERRED_INVESTORS = {"Warren Buffett", "Mohnish Pabrai", "Li Lu", "Seth Klarman"}


def get_manager_holdings(fund_code: str) -> list[dict]:
    """Get current holdings, reported activity, weight, and filing quarter."""
    tickers = []
    try:
        url = f"https://www.dataroma.com/m/holdings.php?m={fund_code}"
        resp = httpx.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        table = soup.find("table", id="grid")
        if not table:
            raise ValueError("Dataroma holdings table missing")

        period_match = re.search(r"Q[1-4] 20\d{2}", soup.get_text(" ", strip=True))
        period = period_match.group(0) if period_match else "Unknown period"

        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) >= 4:
                stock_cell = cells[1].get_text(strip=True)
                # Format: "AAPL- Apple Inc."
                link = cells[1].find("a", href=re.compile(r"stock\.php\?sym="))
                ticker = link["href"].split("sym=")[-1] if link else stock_cell.split("-")[0].strip()
                if re.fullmatch(r"[A-Z0-9]+(?:[.-][A-Z0-9]+)*", ticker):
                    tickers.append({"ticker": ticker.replace(".", "-"), "activity": cells[3].get_text(" ", strip=True) or "Hold", "portfolio_percent": float(cells[2].get_text(strip=True)), "period": period, "source_url": url})
    except Exception as e:
        raise RuntimeError(f"Failed to fetch {fund_code}: {e}") from e

    return tickers


def get_all_superinvestor_holdings() -> dict[str, list[dict]]:
    """Fetch holdings for all tracked superinvestors.

    Returns: {ticker: [holding details, ...]}
    """
    holdings: dict[str, list[dict]] = {}

    for fund_code, name in SUPERINVESTORS.items():
        print(f"   📥 {name}...", end="", flush=True)
        tickers = get_manager_holdings(fund_code)
        print(f" {len(tickers)} holdings")

        for holding in tickers:
            holdings.setdefault(holding["ticker"], []).append({"investor": name, **holding})

    (DATA_DIR / "investor_holdings.json").write_text(json.dumps(holdings, indent=2))
    return holdings


def enrich_with_smart_money(stocks: list[Stock]) -> list[Stock]:
    """Cross-reference screened stocks with superinvestor holdings."""
    holdings = get_all_superinvestor_holdings()

    for stock in stocks:
        activity = holdings.get(stock.ticker, [])
        stock.investor_activity = activity
        stock.superinvestor_holders = [item["investor"] for item in activity]
        # ponytail: latest-quarter snapshot, persist quarterly histories for multi-quarter trends.
        stock.smart_money_score = min(sum(
            (2 if item["investor"] in PREFERRED_INVESTORS else 1)
            * (3 if item["activity"].startswith("Buy") else 2 if item["activity"].startswith("Add") else 0.5 if item["activity"].startswith("Reduce") else 1)
            for item in activity
            if item["portfolio_percent"] >= 0.1
        ), 10.0)

    stocks.sort(key=lambda s: s.smart_money_score, reverse=True)
    return stocks


def run():
    print("🔍 Stage 2: Smart money survey...")
    stocks = load_stocks(DATA_DIR / "01_screened.json")
    stocks = enrich_with_smart_money(stocks)
    held = [s for s in stocks if s.smart_money_score > 0]
    print(f"   {len(held)}/{len(stocks)} held by tracked superinvestors")
    save_stocks(stocks, DATA_DIR / "02_surveyed.json")
    return stocks


if __name__ == "__main__":
    run()
