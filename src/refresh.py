"""Refresh the published watchlist and dated thesis-research candidates."""

from bs4 import BeautifulSoup

from .config import DATA_DIR, DOCS_DIR, RESEARCH_TICKERS
from .models import Stock, save_stocks
from .sentiment import enrich_with_timing
from .summarize import summarize_stocks
from .survey import enrich_with_smart_money
from .build_site import build

def run():
    soup = BeautifulSoup((DOCS_DIR / "index.html").read_text(), "lxml")
    tickers = {node.get_text(strip=True) for node in soup.select(".stock-header .ticker")}
    if not tickers:
        raise ValueError("No published watchlist found; refusing to overwrite the site")
    # Confirmed corporate actions: BK renamed BNY; CTRA merged into DVN;
    # CUK unified into CCL; CPRX acquired for cash and no longer trades.
    tickers = {"BNY" if ticker == "BK" else ticker for ticker in tickers}
    tickers = (tickers | RESEARCH_TICKERS) - {"CPRX", "CTRA", "CUK"}
    stocks = enrich_with_smart_money([Stock(ticker=ticker) for ticker in sorted(tickers)])
    stocks = enrich_with_timing(stocks)
    failed = [stock.ticker for stock in stocks if stock.timing_label == "no data"]
    if failed:
        raise ValueError(f"Incomplete refresh; site was not rebuilt. Failed tickers: {failed}")
    save_stocks(summarize_stocks(stocks), DATA_DIR / "04_final.json")
    build()


if __name__ == "__main__":
    run()
