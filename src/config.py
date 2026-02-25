"""Screening rules and pipeline configuration."""

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

DATA_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)

# --- Screening Rules (Stage 1) ---
# Finviz filter codes: https://finviz.com/screener.ashx
SCREEN_FILTERS = {
    "cap": "midover",          # Market cap > $2B
    "fa_pe": "u25",            # P/E < 25
    "fa_fpe": "u20",           # Forward P/E < 20
    "fa_peg": "u2",            # PEG < 2
    "fa_roe": "o12",           # ROE > 12%
    "fa_de": "u1.5",           # Debt/Equity < 1.5
    "fa_curratio": "o1.2",     # Current ratio > 1.2
    "fa_sales5years": "o10",   # Revenue growth 5yr > 10%
}

# --- Smart Money Sources (Stage 2) ---
SUPERINVESTORS = [
    "Warren Buffett",
    "Bill Ackman",
    "Seth Klarman",
    "David Tepper",
    "Howard Marks",
    "Li Lu",
    "Mohnish Pabrai",
    "Terry Smith",
    "Chuck Akre",
    "Tom Gayner",
]

# --- Alert Thresholds (Stage 3) ---
ALERT_DROP_PCT = -15       # Alert if stock drops this much from 52w high
ALERT_INSIDER_BUYS = 3     # Min insider buy transactions to flag
SHORT_INTEREST_MIN = 5.0   # Min short float % for contrarian signal

# --- Output ---
SITE_TITLE = "Stock Research"
MAX_CANDIDATES = 100       # Cap screener output
