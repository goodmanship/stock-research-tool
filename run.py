#!/usr/bin/env python3
"""Run the full stock research pipeline."""

from src.screen import run as screen
from src.survey import run as survey
from src.sentiment import run as sentiment
from src.summarize import run as summarize
from src.build_site import run as build_site


def main():
    print("=" * 50)
    print("🚀 Stock Research Pipeline")
    print("=" * 50)

    screen()
    survey()
    sentiment()
    summarize()
    build_site()

    print("=" * 50)
    print("✅ Done! Open docs/index.html or push to GitHub Pages")
    print("=" * 50)


if __name__ == "__main__":
    main()
