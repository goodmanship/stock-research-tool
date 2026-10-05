"""Offline regression check: uv run python test_refresh.py."""

from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup

from src.models import Stock
from src.sentiment import enrich_with_timing
from src.survey import enrich_with_smart_money, get_manager_holdings
from src.summarize import assign_verdict
from src.config import RESEARCH_NOTES
from src.build_site import build
from src.dossier import fair_assessment
from src.refresh import run as refresh


with TemporaryDirectory() as directory:
    info = {"currentPrice": 100, "trailingPE": 12, "forwardPE": 10,
            "marketCap": 1000, "freeCashflow": 100, "currency": "USD",
            "financialCurrency": "CNY", "debtToEquity": 5,
            "shortPercentOfFloat": 0.02, "revenueGrowth": 0.15}
    with patch("src.sentiment.yf.Ticker") as ticker, patch("src.sentiment.DATA_DIR", Path(directory)):
        ticker.return_value.info = info
        stock = enrich_with_timing([Stock("PDD", pe=99)])[0]
        assert stock.pe == 12 and stock.debt_equity == 0.05
        assert stock.short_float == 2 and stock.revenue_growth == 15
        assert stock.fcf_yield is None and stock.data_notes
        ticker.return_value.info = {**info, "fiftyTwoWeekHigh": 125, "returnOnEquity": 0.88}
        trimmed = Stock("MU", smart_money_score=10, investor_activity=[{"activity": "Reduce 41.44%", "portfolio_percent": 15.06}])
        trimmed = enrich_with_timing([trimmed])[0]
        assert trimmed.timing_score == 0.4 and trimmed.timing_label == "watch"
        assert assign_verdict(trimmed) == "Watch"
        assert "cycle-normalized" in fair_assessment(trimmed, {})["cautions"][0]
        added = Stock("ADDED", investor_activity=[{"activity": "Add 10%", "portfolio_percent": 1.0}])
        added = enrich_with_timing([added])[0]
        assert abs(added.timing_score - 0.7) < 1e-9 and added.timing_label == "screen signal"
        ticker.return_value.info = {**info, "financialCurrency": "USD", "operatingCashflow": 50}
        assert enrich_with_timing([Stock("FCF")])[0].fcf_yield is None
        ticker.return_value.info = {**info, "financialCurrency": "USD", "trailingPE": 1, "netIncomeToCommon": 100}
        assert enrich_with_timing([Stock("ADR")])[0].pe is None
        ticker.return_value.info = {}
        failed = enrich_with_timing([Stock("FAIL", smart_money_score=10)])[0]
        assert assign_verdict(failed) == "Pass"
    holdings = {"PDD": [{"investor": "Li Lu", "activity": "Add 133.53%", "portfolio_percent": 22.17}],
                "HCC": [{"investor": "Mohnish Pabrai", "activity": "Reduce 3.69%", "portfolio_percent": 43.32}],
                "TINY": [{"investor": "Warren Buffett", "activity": "Buy", "portfolio_percent": 0.0}]}
    with patch("src.survey.get_all_superinvestor_holdings", return_value=holdings):
        stocks = enrich_with_smart_money([Stock("PDD"), Stock("HCC"), Stock("TINY")])
        assert stocks[0].ticker == "PDD" and stocks[0].smart_money_score == 4
        assert stocks[1].smart_money_score == 1
        assert stocks[2].smart_money_score == 0
    html = '<p>Period: Q2 2026</p><table id="grid"><tr><th>Stock</th></tr><tr><td>≡</td><td><a href="/m/stock.php?sym=BRK.B">BRK.B - Berkshire</a></td><td>14.98</td><td>Add 23.46%</td></tr></table>'
    with patch("src.survey.httpx.get") as request:
        request.return_value.text = html
        holding = get_manager_holdings("HC")[0]
        assert holding["ticker"] == "BRK-B" and holding["period"] == "Q2 2026"
        assert holding["portfolio_percent"] == 14.98

    # Generated priorities must agree with dossiers and never revive mechanical buys.
    stocks = [Stock(t, price=100, market_cap=1e9, forward_pe=10, roe=20, fcf_yield=6,
                    verdict="Strong Buy", timing_label="watch") for t in RESEARCH_NOTES]
    stocks.append(Stock("UNREVIEWED", smart_money_score=10, roe=88, fcf_yield=20, timing_label="screen signal"))
    assert assign_verdict(stocks[-1]) == "Watch"
    assert assign_verdict(Stock("GOOGL", timing_label="no data")) == "Pass"
    with patch("src.build_site.load_stocks", return_value=stocks), patch("src.build_site.DOCS_DIR", Path(directory)), patch("src.build_site.build_dossiers", return_value=[]):
        page = BeautifulSoup(build().read_text(), "lxml")
        assert len(page.select("#shortlist .stock-card")) == 6
        assert len(page.select("#conditional .stock-card")) == 4
        assert len(page.select("#background .stock-card")) == len(stocks) - 10
        assert not {"Buy", "Strong Buy"} & {p.get_text(strip=True) for p in page.select(".verdict")}
        research = BeautifulSoup((Path(directory) / "thesis-shortlist.html").read_text(), "lxml")
        assert len(research.select(".card")) == 10
        assert "CROX" in research.get_text() and "Where the analogy breaks" in research.get_text()
    with patch("src.refresh.DOCS_DIR", Path(directory)), patch("src.refresh.DATA_DIR", Path(directory)), patch("src.refresh.RESEARCH_TICKERS", set()), patch("src.refresh.enrich_with_smart_money", side_effect=lambda stocks: stocks) as survey, patch("src.refresh.enrich_with_timing", side_effect=lambda stocks: stocks), patch("src.refresh.build"):
        refresh()
        assert {s.ticker for s in survey.call_args.args[0]} == {s.ticker for s in stocks}

print("Refresh regression checks passed")
