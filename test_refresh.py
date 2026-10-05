"""Offline regression check: uv run python test_refresh.py."""

from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from src.models import Stock
from src.sentiment import enrich_with_timing
from src.survey import enrich_with_smart_money, get_manager_holdings
from src.summarize import assign_verdict


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

print("Refresh regression checks passed")
