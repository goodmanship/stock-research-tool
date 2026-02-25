"""Shared data models for the pipeline."""

from dataclasses import dataclass, field, asdict
from typing import Optional
import json
from pathlib import Path


@dataclass
class Stock:
    ticker: str
    name: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: float = 0
    price: float = 0

    # Fundamentals (Stage 1)
    pe: Optional[float] = None
    forward_pe: Optional[float] = None
    peg: Optional[float] = None
    roe: Optional[float] = None
    debt_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    revenue_growth: Optional[float] = None
    fcf_yield: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None

    # Smart money (Stage 2)
    superinvestor_holders: list[str] = field(default_factory=list)
    smart_money_score: float = 0
    insider_buy_count: int = 0
    insider_sell_count: int = 0
    institutional_pct: Optional[float] = None

    # Sentiment & Timing (Stage 3)
    pct_from_52w_high: Optional[float] = None
    short_float: Optional[float] = None
    timing_score: float = 0  # -1 to 1
    timing_label: str = ""   # "buy now", "wait", "avoid"
    news_summary: str = ""

    # Final (Stage 4)
    verdict: str = ""  # "Strong Buy", "Buy", "Watch", "Pass"
    bull_case: list[str] = field(default_factory=list)
    bear_case: list[str] = field(default_factory=list)
    one_liner: str = ""

    def to_dict(self):
        return asdict(self)


def save_stocks(stocks: list[Stock], path: Path):
    path.parent.mkdir(exist_ok=True)
    with open(path, "w") as f:
        json.dump([s.to_dict() for s in stocks], f, indent=2)


def load_stocks(path: Path) -> list[Stock]:
    with open(path) as f:
        data = json.load(f)
    return [Stock(**d) for d in data]
