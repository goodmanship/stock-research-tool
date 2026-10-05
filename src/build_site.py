"""Build static HTML site from pipeline output."""

from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from .models import load_stocks
from .config import DATA_DIR, DOCS_DIR, TEMPLATES_DIR, SITE_TITLE, RESEARCH_TICKERS, RESEARCH, RESEARCH_NOTES
from .dossier import build as build_dossiers, slugify
from .summarize import summarize_stocks


def build():
    print("🌐 Building static site...")
    stocks = summarize_stocks(load_stocks(DATA_DIR / "04_final.json"))

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True, trim_blocks=True, lstrip_blocks=True)
    template = env.get_template("index.html")

    stock_data = []
    for s in stocks:
        d = s.to_dict()
        d["verdict_class"] = s.verdict.lower().replace(" ", "-")
        d["dossier_href"] = f"stocks/{slugify(s.ticker)}.html" if s.ticker in RESEARCH_TICKERS or (DOCS_DIR / "stocks" / f"{slugify(s.ticker)}.html").exists() else None
        d["research"] = RESEARCH_NOTES.get(s.ticker, {})
        stock_data.append(d)

    shortlist = [s for s in stock_data if s["verdict"] == "Research"]
    conditional = [s for s in stock_data if s["verdict"] == "Watch" and s["research"].get("thesis")]
    background = [s for s in stock_data if s not in shortlist and s not in conditional]
    html = template.render(
        title=SITE_TITLE,
        updated=datetime.now().strftime("%Y-%m-%d %H:%M"),
        total=len(stocks),
        reviewed=RESEARCH["reviewed"],
        shortlist=shortlist,
        conditional=conditional,
        background=background,
    )

    out = DOCS_DIR / "index.html"
    out.write_text("\n".join(line.rstrip() for line in html.splitlines()) + "\n")
    by_ticker = {s["ticker"]: s for s in stock_data}
    comparisons = [(s, by_ticker[s["research"]["analogue_of"]]) for s in stock_data if s["research"].get("new")]
    research_html = env.get_template("research.html").render(
        research=RESEARCH, shortlist=shortlist, conditional=conditional,
        comparisons=comparisons, decisions=[s for s in stock_data if s["research"].get("reason")],
    )
    (DOCS_DIR / "thesis-shortlist.html").write_text("\n".join(line.rstrip() for line in research_html.splitlines()) + "\n")
    dossier_files = build_dossiers()
    print(f"   ✅ Written to {out}")
    print(f"   ✅ Written {len(dossier_files)} dossier pages")
    return out


def run():
    build()


if __name__ == "__main__":
    run()
