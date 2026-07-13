#!/usr/bin/env python3
"""Verify the Streamlit learning UI renders the v1 first-screen loop."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit.testing.v1 import AppTest  # noqa: E402


REQUIRED_BUTTONS = (
    "Explore HBB",
    "Try BRCA1",
    "Try TP53",
    "Search any gene",
    "Simulate mutation",
)
REQUIRED_COPY = (
    "Start with a real gene story",
    "HBB",
    "Tap a gene card to inspect it",
    "Tap a central dogma step",
    "Chromosome location",
    "Two-minute mutation lesson",
    "Missense",
    "Nonsense",
    "Frameshift",
    "Effect: missense",
    "Effect: nonsense",
    "Effect: frameshift",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def rendered_ui_text(app: AppTest) -> str:
    pieces: list[str] = []
    for collection_name in (
        "title",
        "header",
        "subheader",
        "caption",
        "markdown",
        "button",
        "segmented_control",
        "selectbox",
    ):
        for item in getattr(app, collection_name):
            pieces.append(str(getattr(item, "value", "")))
            pieces.append(str(getattr(item, "label", "")))
    return "\n".join(pieces)


def main() -> int:
    try:
        app = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
        app.run(timeout=30)

        require(not app.exception, f"Streamlit rendered with {len(app.exception)} exception(s).")

        buttons = {str(getattr(button, "label", "")).splitlines()[0] for button in app.button}
        for label in REQUIRED_BUTTONS:
            require(label in buttons, f"Missing guided first-screen button: {label}")

        text = rendered_ui_text(app)
        for phrase in REQUIRED_COPY:
            require(phrase in text, f"Missing Streamlit learning copy: {phrase}")

        print("ok Streamlit guided start + two-minute mutation lesson")
    except (AssertionError, RuntimeError, ValueError) as exc:
        print(f"Streamlit UI verification failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
