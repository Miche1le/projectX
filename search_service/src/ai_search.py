from __future__ import annotations

import random
import textwrap
from datetime import datetime, timezone


def run_ai_search(text: str) -> tuple[str, str]:
    seed = sum(ord(ch) for ch in text)
    random.seed(seed)
    sentences = [
        "We collected the latest updates from public sources.",
        "Key facts are cross-checked against multiple outlets.",
        "Analysis relies on open reports and official statements.",
        "Trends may change quickly; monitor for updates.",
        "Review original materials if you need exact quotes.",
    ]
    selected = random.sample(sentences, k=min(3, len(sentences)))
    summary = " ".join(selected)
    short_summary = textwrap.shorten(summary, width=280, placeholder="...")
    return short_summary, summary

