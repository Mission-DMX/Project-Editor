#!/usr/bin/env python3
"""
add_missing_ofl_colours_local_fixed_v2.py

Usage
-----
    python add_missing_ofl_colours_local_fixed_v2.py <path_to_csv> <path_to_fixtures_dir>

The script:

1. reads the existing CSV (name;hue;saturation;intensity)
2. walks a *local* copy of the Open‑Fixture‑Library ``fixtures`` directory,
   reads every ``*.json`` file and extracts **all colour names** that appear
   anywhere under the keys ``color`` or ``colour``.
3. looks each missing colour up on https://www.colornames.org
4. appends the newly‑found colours to the CSV.

Dependencies
------------
    pip install requests beautifulsoup4
"""

import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, Set, Tuple

import requests
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
COLORNAMES_URL = "https://www.colornames.org/color/{}"   # {} → colour name (URL‑escaped)
REQUEST_DELAY = 0.5          # seconds – be gentle to colornames.org
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
# ----------------------------------------------------------------------


def read_csv(csv_path: Path) -> Dict[str, Tuple[float, float, float]]:
    """Read the CSV and return a dict ``name → (hue, sat, intensity)``."""
    colours = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.reader(f, delimiter=";"):
            if len(row) != 4:
                continue
            name, hue, sat, val = row
            try:
                colours[name.strip().lower()] = (float(hue), float(sat), float(val))
            except ValueError:
                continue
    return colours


def append_to_csv(csv_path: Path, rows: Set[Tuple[str, float, float, float]]) -> None:
    """Append the supplied rows to the CSV file."""
    if not rows:
        print("✅ No new colours – CSV already up‑to‑date.")
        return

    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        for name, hue, sat, val in sorted(rows):
            writer.writerow([name, f"{hue:.1f}", f"{sat:.3f}", f"{val:.3f}"])
    print(f"✅ Added {len(rows)} colour(s) to {csv_path}.")


# ----------------------------------------------------------------------
# Local fixture handling
# ----------------------------------------------------------------------
def list_fixture_files(root: Path) -> Set[Path]:
    """Return a set of all ``*.json`` files under *root* (recursively)."""
    return {p for p in root.rglob("*.json") if p.is_file()}


def fetch_fixture_json(file_path: Path) -> dict:
    """Load a fixture JSON file from the local filesystem."""
    with file_path.open(encoding="utf-8") as f:
        return json.load(f)


def _collect_colour_names(obj, out: Set[str]) -> None:
    """Recursively walk *obj* and add every string value whose key is
    ``color`` or ``colour`` (case‑insensitive) to *out*."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in ("color", "colour"):
                if isinstance(v, str):
                    out.add(v.strip().lower())
            _collect_colour_names(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_colour_names(item, out)


def colours_from_fixture(fixture: dict) -> Set[str]:
    """Return the set of colour names used anywhere inside the fixture JSON."""
    result: Set[str] = set()
    _collect_colour_names(fixture, result)
    return result


# ----------------------------------------------------------------------
# colornames.org scraper
# ----------------------------------------------------------------------
def _scrape_page(url: str) -> BeautifulSoup:
    """GET the page with a proper User‑Agent and return a BeautifulSoup object."""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def lookup_colour(name: str) -> Tuple[float, float, float]:
    """
    Scrape https://www.colornames.org/color/<name> and extract:
        Hue (°), Saturation (%), Value (%)

    Returns (hue, saturation, intensity) where saturation and intensity are
    normalised to the range 0‑1.

    The function tries two URL forms:
        1. the raw name (e.g. ``cyan``)
        2. the name with spaces replaced by hyphens
           (e.g. ``cold white`` → ``cold-white``)

    If both attempts fail a ``ValueError`` is raised.
    """
    # Normalise the name for the URL
    raw = name.strip().lower()
    hyphenated = raw.replace(" ", "-")

    for candidate in (raw, hyphenated):
        url = COLORNAMES_URL.format(requests.utils.quote(candidate))
        try:
            soup = _scrape_page(url)
        except requests.HTTPError as exc:
            # 403/404 → try the next candidate
            if exc.response.status_code in (403, 404):
                continue
            raise

        # Helper to pull a numeric value from the table
        def _value(label: str) -> float:
            th = soup.find("th", string=lambda s: s and label in s)
            if not th:
                raise ValueError(f"{label} not found for colour '{name}'")
            td = th.find_next_sibling("td")
            if not td:
                raise ValueError(f"{label} value missing for colour '{name}'")
            txt = td.get_text(strip=True).replace("°", "").replace("%", "")
            return float(txt)

        hue = _value("Hue")
        sat = _value("Saturation") / 100.0
        val = _value("Value") / 100.0
        return hue, sat, val

    # If we get here none of the candidates succeeded
    raise ValueError(f"Could not retrieve colour data for '{name}' (tried '{raw}' and '{hyphenated}')")


# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main(csv_file: str, fixtures_dir: str) -> None:
    csv_path = Path(csv_file)
    fixtures_root = Path(fixtures_dir)

    if not csv_path.is_file():
        sys.exit(f"❌ CSV file not found: {csv_path}")
    if not fixtures_root.is_dir():
        sys.exit(f"❌ Fixtures directory not found: {fixtures_root}")

    # 1️⃣ Load existing colour definitions
    existing = read_csv(csv_path)
    print(f"🔎 Loaded {len(existing)} colour(s) from CSV.")

    # 2️⃣ Gather every colour name used in the local OFL fixtures
    fixture_files = list_fixture_files(fixtures_root)
    print(f"📂 Found {len(fixture_files)} fixture JSON files under {fixtures_root}.")

    all_ofl_colours: Set[str] = set()
    for file_path in fixture_files:
        try:
            fixture = fetch_fixture_json(file_path)
            all_ofl_colours.update(colours_from_fixture(fixture))
        except Exception as exc:
            print(f"⚠️  Could not process {file_path}: {exc}")

    print(f"🎨 Extracted {len(all_ofl_colours)} distinct colour name(s) from fixtures.")

    # 3️⃣ Determine which colours are missing from the CSV
    missing = {c for c in all_ofl_colours if c not in existing}
    print(f"❓ {len(missing)} colour(s) are missing and will be looked up.")

    # 4️⃣ Look them up on colornames.org
    new_rows: Set[Tuple[str, float, float, float]] = set()
    for colour_name in missing:
        try:
            hue, sat, val = lookup_colour(colour_name)
            new_rows.add((colour_name, hue, sat, val))
            print(f"✅ Found {colour_name}: hue={hue:.1f}, sat={sat:.3f}, val={val:.3f}")
        except Exception as exc:
            print(f"❌ Could not retrieve data for '{colour_name}': {exc}")
        finally:
            time.sleep(REQUEST_DELAY)   # be gentle to colornames.org

    # 5️⃣ Append the new rows to the CSV
    append_to_csv(csv_path, new_rows)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(
            "Usage: python add_missing_ofl_colours_local_fixed_v2.py <path_to_csv> <path_to_fixtures_dir>"
        )
    main(sys.argv[1], sys.argv[2])