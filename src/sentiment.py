"""Stage 3: Sentiment & timing signals."""

import yfinance as yf
import json
from datetime import datetime, timezone
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
            if not info.get("currentPrice") and not info.get("regularMarketPrice"):
                raise ValueError("No current market price returned")
            stock.market_data_at = datetime.fromtimestamp(info["regularMarketTime"], timezone.utc).isoformat() if info.get("regularMarketTime") else ""
            (DATA_DIR / f"{stock.ticker}_info.json").write_text(json.dumps(info, default=str))
            stock.name = info.get("longName") or info.get("shortName") or stock.name
            stock.sector = info.get("sector") or stock.sector
            stock.industry = info.get("industry") or stock.industry
            stock.pe = info.get("trailingPE")
            income = info.get("netIncomeToCommon")
            mcap = info.get("marketCap")
            if info.get("financialCurrency") == info.get("currency") and stock.pe and income and income > 0 and mcap and not 0.5 <= stock.pe / (mcap / income) <= 2:
                stock.pe = None
                stock.data_notes.append("Trailing P/E omitted: Yahoo EPS and market-cap/net-income imply inconsistent share units; verify ADR ratio or corporate actions.")
            stock.revenue_growth = info.get("revenueGrowth") * 100 if info.get("revenueGrowth") is not None else None
            stock.current_ratio = info.get("currentRatio")
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
            if stock.debt_equity is not None:
                stock.debt_equity /= 100  # Yahoo reports debt/equity as a percentage.
            stock.gross_margin = (info.get("grossMargins") or 0) * 100 if info.get("grossMargins") else None
            stock.net_margin = (info.get("netIncomeToRevenue") or info.get("profitMargins") or 0) * 100 if info.get("profitMargins") else None
            stock.short_float = info.get("shortPercentOfFloat")
            if stock.short_float is not None:
                stock.short_float *= 100
            stock.institutional_pct = (info.get("heldPercentInstitutions") or 0) * 100 if info.get("heldPercentInstitutions") else None
            stock.fcf_yield = None
            mcap = info.get("marketCap")
            fcf = info.get("freeCashflow")
            if info.get("financialCurrency") != info.get("currency"):
                stock.data_notes.append("FCF yield omitted: financial statements and market cap use different currencies.")
            elif stock.industry.startswith(("Banks -", "Insurance -", "REIT -")):
                stock.data_notes.append("FCF yield omitted: conventional operating FCF is not a suitable valuation measure for this financial/REIT business.")
            elif fcf is not None and info.get("operatingCashflow") is not None and fcf > info["operatingCashflow"]:
                stock.data_notes.append("FCF yield omitted: Yahoo free cash flow exceeds operating cash flow; verify against company statements.")
            elif mcap and fcf is not None and mcap > 0:
                stock.fcf_yield = (fcf / mcap) * 100
            stock.market_cap = mcap or stock.market_cap

            # Price/accumulation screen; neither drawdown nor shorts establish value.
            score = 0.0
            if stock.pct_from_52w_high is not None and stock.pct_from_52w_high <= ALERT_DROP_PCT:
                score += 0.4  # beaten down
            if any(item["activity"].startswith(("Buy", "Add")) and item["portfolio_percent"] >= 0.1 for item in stock.investor_activity):
                score += 0.3
            if stock.fcf_yield and stock.fcf_yield > 5:
                score += 0.1  # strong cash generation

            stock.timing_score = min(score, 1.0)
            if score >= 0.6:
                stock.timing_label = "screen signal"
            elif score >= 0.3:
                stock.timing_label = "watch"
            else:
                stock.timing_label = "wait"

        except Exception as e:
            print(f"   ⚠️  {stock.ticker}: {e}")
            stock.data_notes.append(f"Market refresh failed: {e}")
            stock.timing_label = "no data"

    return stocks


def run():
    print("📈 Stage 3: Sentiment & timing...")
    stocks = load_stocks(DATA_DIR / "02_surveyed.json")
    stocks = enrich_with_timing(stocks)
    signals = [s for s in stocks if s.timing_label == "screen signal"]
    print(f"   {len(signals)} price/accumulation screen signals")
    save_stocks(stocks, DATA_DIR / "03_sentiment.json")
    return stocks


if __name__ == "__main__":
    run()
