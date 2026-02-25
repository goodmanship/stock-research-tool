# Stock Research Tool — PRD

_Draft v0.1 — 2026-02-20_

## Vision

A personal research pipeline that takes you from "the entire market" to "here are 10-20 companies I'm confident in" — with minimal manual work. Think of it as a funnel:

```
Thousands of stocks
    → Screen (quantitative filter)
        → Survey (what are smart money doing?)
            → Analyze (sentiment + timing)
                → Summarize (buy case in plain English)
                    → Your Portfolio Watchlist
```

## Core Workflow

### Stage 1: Screen — "What's worth looking at?"
- **Source:** Finviz screener (or equivalent API)
- **Input:** A saved set of screening rules (you define these)
- **Examples:** P/E < 20, revenue growth > 15%, market cap > $1B, ROE > 15%, debt/equity < 1
- **Output:** ~50-100 candidates that pass your quantitative bar
- **Frequency:** Weekly or on-demand

### Stage 2: Survey — "What are the smart people doing?"
- **Sources:**
  - Dataroma (superinvestor portfolios — Buffett, Ackman, etc.)
  - WhaleWisdom (13F filings, institutional holdings)
  - SEC EDGAR (insider buying/selling)
  - Optional: OpenInsider, Fintel
- **Logic:**
  - Cross-reference Stage 1 output with superinvestor holdings
  - Flag stocks being accumulated by multiple gurus
  - Flag recent insider buying (clusters > one-offs)
  - Score by conviction: new position > added to > held steady > trimmed
- **Output:** Ranked list with "smart money score" — who owns it, are they buying or selling, how concentrated is it

### Stage 3: Sentiment & Timing — "Is now a good time?"
- **Sources:**
  - Recent news (earnings surprises, analyst upgrades/downgrades)
  - Price action (52-week range position, recent drawdown %)
  - Short interest (contrarian signal)
  - Social sentiment (Reddit/StockTwits/Twitter — lightweight, not primary)
  - Earnings calendar (upcoming catalysts)
  - Fear & Greed / VIX context
- **Logic:**
  - Contrarian scoring: stock is down 20%+ from highs BUT fundamentals haven't deteriorated = interesting
  - "Hated + held by smart money" = strongest signal
  - Upcoming earnings within 2 weeks = flag (opportunity or risk)
- **Output:** Timing score (buy now / wait / avoid) with rationale

### Stage 4: Summarize — "Give me the buy case"
- **For each candidate that survives Stages 1-3, generate:**
  - **One-liner:** What the company does
  - **Bull case:** 3-5 bullet points
  - **Bear case:** 2-3 risks
  - **Smart money:** Who owns it, recent activity
  - **Timing:** Why now (or why wait)
  - **Key metrics:** P/E, revenue growth, margins, debt, FCF yield
  - **Price target range:** Based on analyst consensus
  - **Verdict:** Strong buy / Buy / Watch / Pass
- **Format:** Clean, scannable — something you can read in 2 min per stock

## Architecture Options

### Option A: CLI Pipeline (simplest)
```
Python scripts per stage → JSON intermediate files → Markdown output
```
- `screen.py` — hits Finviz, outputs candidates.json
- `survey.py` — hits Dataroma/WhaleWisdom/EDGAR, enriches candidates
- `sentiment.py` — news/price/short interest analysis
- `summarize.py` — LLM-powered synthesis → markdown reports
- `run.py` — orchestrates the full pipeline

**Pros:** Fast to build, easy to iterate, runs from terminal
**Cons:** No UI, manual trigger

### Option B: Web App (richer)
```
FastAPI backend → React/Next.js frontend → SQLite/Postgres
```
- Dashboard with your watchlist
- Click-to-refresh per stock or full pipeline
- Historical tracking (see how scores change over time)
- Portfolio view with allocation suggestions

**Pros:** Visual, trackable, shareable
**Cons:** More to build and maintain

### Option C: Hybrid (recommended)
```
CLI pipeline (Option A) → generates static site or Obsidian notes
```
- Pipeline runs on schedule (cron) or on-demand
- Outputs to your Obsidian vault as structured notes
- Each stock = one note with all the data
- Dashboard note with ranked table linking to each
- Tag system: #strong-buy, #watch, #pass

**Pros:** Best of both — automation + browsable + already in your workflow
**Cons:** Obsidian-specific (but you already use it)

## Data Sources & Access

| Source | Access | Cost | Notes |
|--------|--------|------|-------|
| Finviz | Scrape or Elite API ($25/mo) | Free/Paid | Screener params via URL |
| Dataroma | Scrape | Free | Superinvestor 13F data |
| WhaleWisdom | API or scrape | Free tier exists | 13F institutional data |
| SEC EDGAR | Official API | Free | XBRL filings, insider tx |
| OpenInsider | Scrape | Free | Insider buying/selling |
| Yahoo Finance | yfinance Python lib | Free | Price, fundamentals |
| Alpha Vantage | API key | Free tier (25/day) | Fundamentals + news |
| Financial Modeling Prep | API | Free tier exists | Good fundamentals API |
| News/Sentiment | Various | Mixed | NewsAPI, Google News RSS |

## Screening Rules (Starting Point — Iterate)

```yaml
# Value + Quality + Growth hybrid
market_cap: "> 1B"
pe_ratio: "< 25"
forward_pe: "< 20"
peg_ratio: "< 2"
revenue_growth_yoy: "> 10%"
roe: "> 12%"
debt_equity: "< 1.5"
current_ratio: "> 1.2"
free_cash_flow: "> 0"
institutional_ownership: "> 30%"
# Optional contrarian filters
price_vs_52w_high: "< -15%"  # at least 15% off highs
short_float: "> 5%"          # some shorts to squeeze
```

## Decisions (2026-06-26)

1. **Output:** Static HTML → GitHub Pages (viewable on phone anywhere)
2. **Screening rules:** Start with defaults, iterate over time
3. **Alerts:** Yes — "stock X dropped 15% and Buffett owns it" style notifications
4. **Summaries:** Template-based (no LLM cost). Add Ollama later if needed.
5. **Backtesting:** TBD
6. **Sector diversification:** TBD

## MVP Scope (v0.1)

If we build this iteratively:

1. **Week 1:** Finviz screener + Yahoo Finance fundamentals → candidates list
2. **Week 2:** Dataroma/WhaleWisdom overlay → smart money scoring
3. **Week 3:** Sentiment + timing layer (price action, news, short interest)
4. **Week 4:** LLM summarizer → polished buy case reports
5. **Ongoing:** Refine screening rules based on what surfaces good picks

## Tech Stack (recommended)

- **Python 3** — data pipeline
- **yfinance** — market data
- **BeautifulSoup/httpx** — scraping where needed
- **Claude API or local LLM** — summary generation
- **SQLite** — store historical data/scores
- **Markdown output** — Obsidian or standalone
- **Cron/systemd timer** — scheduled runs
