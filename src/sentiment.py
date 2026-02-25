"""Stage 3: Sentiment & timing signals."""

import yfinance as yf
from .models import Stock, load_stocks, save_stocks
from .config import DATA_DIR, ALERT_DROP_PCT


def enrich_with_timing(stocks: list[Stock]) -> list[Stock]:
    """Add price action and timing signals via yfinance."""
    tickers = [s.ticker for s in stocks]
    print(f"   Fetching market data for {len(tickers)} tickers...")

    # Batch fetch
    for stock in stocks:
        try:
            info = yf.Ticker(stock.ticker).info
            high_52w = info.get("fiftyTwoWeekHigh")
            price = info.get("currentPrice") or info.get("regularMarketPrice")

            if price:
                stock.price = price
            if price and high_52w and high_52w > 0:
                stock.pct_from_52w_high = ((price - high_52w) / high_52w) * 100

            stock.forward_pe = info.get("forwardPE")
            stock.peg = info.get("pegRatio")
            stock.roe = (info.get("returnOnEquity") or 0) * 100 if info.get("returnOnEquity") else None
            stock.debt_equity = info.get("debtToEquity")
            if stock.debt_equity and stock.debt_equity > 10:
                stock.debt_equity = stock.debt_equity / 100  # normalize
            stock.gross_margin = (info.get("grossMargins") or 0) * 100 if info.get("grossMargins") else None
            stock.net_margin = (info.get("netIncomeToRevenue") or info.get("profitMargins") or 0) * 100 if info.get("profitMargins") else None
            stock.short_float = info.get("shortPercentOfFloat")
            if stock.short_float and stock.short_float < 1:
                stock.short_float *= 100
            stock.institutional_pct = (info.get("heldPercentInstitutions") or 0) * 100 if info.get("heldPercentInstitutions") else None
            stock.fcf_yield = None
            mcap = info.get("marketCap")
            fcf = info.get("freeCashflow")
            if mcap and fcf and mcap > 0:
                stock.fcf_yield = (fcf / mcap) * 100
            stock.market_cap = mcap or stock.market_cap

            # Timing score: contrarian = down from highs + smart money holds
            score = 0.0
            if stock.pct_from_52w_high is not None and stock.pct_from_52w_high <= ALERT_DROP_PCT:
                score += 0.4  # beaten down
            if stock.smart_money_score > 0:
                score += 0.3
            if stock.short_float and stock.short_float > 5:
                score += 0.2  # contrarian squeeze potential
            if stock.fcf_yield and stock.fcf_yield > 5:
                score += 0.1  # strong cash generation

            stock.timing_score = min(score, 1.0)
            if score >= 0.6:
                stock.timing_label = "buy now"
            elif score >= 0.3:
                stock.timing_label = "watch"
            else:
                stock.timing_label = "wait"

        except Exception as e:
            print(f"   ⚠️  {stock.ticker}: {e}")
            stock.timing_label = "no data"

    return stocks


def run():
    print("📈 Stage 3: Sentiment & timing...")
    stocks = load_stocks(DATA_DIR / "02_surveyed.json")
    stocks = enrich_with_timing(stocks)
    buy_now = [s for s in stocks if s.timing_label == "buy now"]
    print(f"   {len(buy_now)} flagged as 'buy now'")
    save_stocks(stocks, DATA_DIR / "03_sentiment.json")
    return stocks


if __name__ == "__main__":
    run()
