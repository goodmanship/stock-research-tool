"""Build static HTML site from pipeline output."""

from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from .models import load_stocks
from .config import DATA_DIR, DOCS_DIR, TEMPLATES_DIR, SITE_TITLE
from .dossier import build as build_dossiers, slugify


def build():
    print("🌐 Building static site...")
    stocks = load_stocks(DATA_DIR / "04_final.json")

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("index.html")

    # Prep template data
    verdict_counts = {}
    for s in stocks:
        verdict_counts[s.verdict] = verdict_counts.get(s.verdict, 0) + 1

    stock_data = []
    for s in stocks:
        d = s.to_dict()
        d["verdict_class"] = s.verdict.lower().replace(" ", "-")
        d["dossier_href"] = f"stocks/{slugify(s.ticker)}.html" if s.verdict == "Strong Buy" else None
        stock_data.append(d)

    html = template.render(
        title=SITE_TITLE,
        updated=datetime.now().strftime("%Y-%m-%d %H:%M"),
        total=len(stocks),
        strong_buy=verdict_counts.get("Strong Buy", 0),
        buy=verdict_counts.get("Buy", 0),
        watch=verdict_counts.get("Watch", 0),
        pass_=verdict_counts.get("Pass", 0),
        stocks=stock_data,
    )

    out = DOCS_DIR / "index.html"
    out.write_text(html)
    dossier_files = build_dossiers()
    print(f"   ✅ Written to {out}")
    print(f"   ✅ Written {len(dossier_files)} dossier pages")
    return out


def run():
    build()


if __name__ == "__main__":
    run()
