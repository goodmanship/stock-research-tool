"""Stage 1: Finviz quantitative screening."""

import httpx
from bs4 import BeautifulSoup
from .models import Stock, save_stocks
from .config import SCREEN_FILTERS, DATA_DIR, MAX_CANDIDATES

FINVIZ_URL = "https://finviz.com/screener.ashx"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}


def build_filter_string(filters: dict) -> str:
    return ",".join(f"{k}_{v}" for k, v in filters.items())


def scrape_finviz(filters: dict, max_results: int = MAX_CANDIDATES) -> list[Stock]:
    """Scrape Finviz screener results."""
    stocks = []
    offset = 1

    while len(stocks) < max_results:
        params = {
            "v": "111",  # Overview view
            "f": build_filter_string(filters),
            "r": str(offset),
        }

        resp = httpx.get(FINVIZ_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Find the results table
        table = soup.find("table", class_="screener_table") or soup.find(
            "table", {"id": "screener-views-table"}
        )
        if not table:
            # Try alternate: look for rows with ticker links
            rows = soup.select("tr.screener-body-table-nw")
            if not rows:
                break
        else:
            rows = table.find_all("tr")[1:]  # skip header

        if not rows:
            break

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 11:
                continue
            try:
                ticker = cells[1].get_text(strip=True)
                name = cells[2].get_text(strip=True)
                sector = cells[3].get_text(strip=True)
                industry = cells[4].get_text(strip=True)
                market_cap = _parse_market_cap(cells[6].get_text(strip=True))
                pe = _parse_float(cells[7].get_text(strip=True))
                price = _parse_float(cells[8].get_text(strip=True))

                stocks.append(Stock(
                    ticker=ticker,
                    name=name,
                    sector=sector,
                    industry=industry,
                    market_cap=market_cap,
                    pe=pe,
                    price=price or 0,
                ))
            except (IndexError, ValueError):
                continue

            if len(stocks) >= max_results:
                break

        offset += 20
        if len(rows) < 20:
            break

    return stocks


def _parse_float(s: str) -> float | None:
    s = s.replace("%", "").replace(",", "").strip()
    if s in ("-", "", "N/A"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_market_cap(s: str) -> float:
    s = s.strip().upper()
    multipliers = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}
    for suffix, mult in multipliers.items():
        if s.endswith(suffix):
            return float(s[:-1]) * mult
    return _parse_float(s) or 0


def run():
    print("📊 Stage 1: Screening via Finviz...")
    stocks = scrape_finviz(SCREEN_FILTERS)
    print(f"   Found {len(stocks)} candidates")
    save_stocks(stocks, DATA_DIR / "01_screened.json")
    return stocks


if __name__ == "__main__":
    run()
