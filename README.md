# Stock Research Tool

Personal stock research pipeline: screen → survey smart money → timing signals → buy case summaries.

Output: static HTML site deployed to GitHub Pages.

## Quick Start

Refresh the existing published watchlist plus the investor-sourced research list:

```bash
uv sync
uv run python -m src.refresh
uv run python test_refresh.py
python -m http.server 8080 -d docs/
```

Investor activity includes the filing quarter, portfolio weight, and reported
buy/add/hold/reduce status. Buffett/Berkshire, Pabrai, Li Lu, and Klarman receive
double weight; new positions and additions score above unchanged holdings,
and trims score below them. Positions below 0.1% of a manager's portfolio are
displayed but do not score. This is a latest-quarter accumulation snapshot,
not a multi-quarter trend or an estimate of investor cost basis.
Foreign-currency FCF yields and conventional FCF yields for banks, insurers,
and REITs are omitted. Inconsistent P/E share units and FCF above operating
cash flow are flagged rather than ranked as bargains. Raw data is saved locally in `data/`.
The refresh stops before rebuilding the site if any market quote is missing.

The home page shows six editorial research priorities, with conditional watches
and the broader pool behind expandable sections. `research/shortlist.json`
stores the dated thesis, evidence, valuation checks, risks and source links;
`docs/thesis-shortlist.html` compares five smaller-company ideas with their anchors.
Research / Watch / Pass are research priorities, not trade recommendations.
Quantitative signals cannot generate Buy / Strong Buy labels. Timing only credits
material reported buys/adds, not unchanged or reduced holdings or short interest.
Refreshing quotes does not update the dated thesis or historical valuation notes.

```bash
# Install dependencies
pip install -r requirements.txt

# Run full pipeline
python run.py

# Run individual stages
python -m src.screen        # Finviz screener → candidates
python -m src.survey        # Smart money overlay
python -m src.sentiment     # Timing & sentiment signals
python -m src.summarize     # Generate buy case reports
python -m src.build_site    # Build static HTML site

# Serve locally
python -m http.server 8080 -d docs/
```

## Architecture

```
src/
  screen.py      — Finviz quantitative screening
  survey.py      — Superinvestor/insider cross-reference
  sentiment.py   — Price action, short interest, news
  summarize.py   — Template-based buy case generation
  build_site.py  — Static HTML site builder
  models.py      — Shared data models
  config.py      — Screening rules & settings

data/            — Intermediate JSON (gitignored)
docs/            — Generated static site (GitHub Pages source)
templates/       — HTML templates (Jinja2)
```
