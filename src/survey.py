"""Stage 2: Smart money cross-reference (Dataroma + insider buying)."""

import httpx
from bs4 import BeautifulSoup
from .models import Stock, load_stocks, save_stocks
from .config import DATA_DIR, SUPERINVESTORS

DATAROMA_URL = "https://www.dataroma.com/m/holdings.php"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}


def get_superinvestor_holdings() -> dict[str, list[str]]:
    """Scrape Dataroma for superinvestor holdings.

    Returns: {ticker: [investor_name, ...]}
    """
    holdings: dict[str, list[str]] = {}

    # Dataroma "superinvestors" page lists all tracked managers
    try:
        resp = httpx.get(
            "https://www.dataroma.com/m/home.php",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Find manager links
        for link in soup.select("a[href*='holdings.php']"):
            manager_name = link.get_text(strip=True)
            if not any(s.lower() in manager_name.lower() for s in SUPERINVESTORS):
                continue

            manager_url = "https://www.dataroma.com/m/" + link["href"]
            try:
                mresp = httpx.get(manager_url, headers=HEADERS, timeout=15)
                mresp.raise_for_status()
                msoup = BeautifulSoup(mresp.text, "lxml")

                for row in msoup.select("table#grid tr")[1:]:
                    cells = row.find_all("td")
                    if len(cells) >= 3:
                        ticker_el = cells[1].find("a")
                        if ticker_el:
                            ticker = ticker_el.get_text(strip=True).upper()
                            holdings.setdefault(ticker, []).append(manager_name)
            except Exception:
                continue

    except Exception as e:
        print(f"   ⚠️  Dataroma scrape failed: {e}")

    return holdings


def enrich_with_smart_money(stocks: list[Stock]) -> list[Stock]:
    """Cross-reference screened stocks with superinvestor holdings."""
    print("   Fetching superinvestor holdings from Dataroma...")
    holdings = get_superinvestor_holdings()

    for stock in stocks:
        investors = holdings.get(stock.ticker, [])
        stock.superinvestor_holders = investors
        # Simple scoring: more holders = higher score
        stock.smart_money_score = len(investors) * 2.0

    # Sort by smart money score descending
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
