# Stock Research Tool

Personal stock research pipeline: screen → survey smart money → timing signals → buy case summaries.

Output: static HTML site deployed to GitHub Pages.

## Quick Start

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
