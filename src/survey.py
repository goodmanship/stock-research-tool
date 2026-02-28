"""Stage 2: Smart money cross-reference (Dataroma superinvestor holdings)."""

import httpx
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
    "SEQUX": "Ruane Cunniff (Sequoia)",
    "GLRE": "David Einhorn",
    "ic": "Carl Icahn",
    "tp": "Daniel Loeb",
}


def get_manager_holdings(fund_code: str) -> list[str]:
    """Get list of tickers held by a manager."""
    tickers = []
    try:
        url = f"https://www.dataroma.com/m/holdings.php?m={fund_code}"
        resp = httpx.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        table = soup.find("table", id="grid")
        if not table:
            return tickers

        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) >= 2:
                stock_cell = cells[1].get_text(strip=True)
                # Format: "AAPL- Apple Inc."
                ticker = stock_cell.split("-")[0].strip()
                if ticker and ticker.isalpha():
                    tickers.append(ticker.upper())
    except Exception as e:
        print(f"   ⚠️  Failed to fetch {fund_code}: {e}")

    return tickers


def get_all_superinvestor_holdings() -> dict[str, list[str]]:
    """Fetch holdings for all tracked superinvestors.

    Returns: {ticker: [investor_name, ...]}
    """
    holdings: dict[str, list[str]] = {}

    for fund_code, name in SUPERINVESTORS.items():
        print(f"   📥 {name}...", end="", flush=True)
        tickers = get_manager_holdings(fund_code)
        print(f" {len(tickers)} holdings")

        for ticker in tickers:
            holdings.setdefault(ticker, []).append(name)

    return holdings


def enrich_with_smart_money(stocks: list[Stock]) -> list[Stock]:
    """Cross-reference screened stocks with superinvestor holdings."""
    holdings = get_all_superinvestor_holdings()

    for stock in stocks:
        investors = holdings.get(stock.ticker, [])
        stock.superinvestor_holders = investors
        # Scoring: each holder = 2 points, diminishing
        stock.smart_money_score = min(len(investors) * 2.0, 10.0)

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
