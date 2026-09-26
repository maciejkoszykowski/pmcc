"""Test Google PageSpeed Insights strony PMCC -> data/pagespeed.yml.

Użycie (z dowolnego folderu), przed budowaniem strony (hugo) i wgraniem na serwer:
    python scripts/pagespeed-test.py

Co robi:
    1. czyta adres strony (psi_url) z data/statystyki.yml i klucz API z psi-key.txt (static/ albo public/)
    2. robi test na telefon i na komputer (szybkość, SEO, dostępność, dobre praktyki + czasy ładowania)
    3. zapisuje wyniki z datą do data/pagespeed.yml

Strona /statystyki pokazuje te wyniki jako "wyniki z dnia wgrania strony".
Google testuje stronę, która jest w tej chwili na serwerze (czyli wersję sprzed nowego wgrania).
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(ROOT, "data", "statystyki.yml")
KEY_FILES = [os.path.join(ROOT, "static", "psi-key.txt"), os.path.join(ROOT, "public", "psi-key.txt")]
OUT_FILE = os.path.join(ROOT, "data", "pagespeed.yml")

API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
CATEGORIES = ["performance", "seo", "accessibility", "best-practices"]
METRICS = ["largest-contentful-paint", "first-contentful-paint", "total-blocking-time", "cumulative-layout-shift"]


def read_url():
    with open(SETTINGS_FILE, encoding="utf-8") as f:
        m = re.search(r'^psi_url\s*:\s*"([^"]+)"', f.read(), re.M)
    if not m:
        sys.exit(f"Brak psi_url w {SETTINGS_FILE}")
    return m.group(1)


def read_key():
    for path in KEY_FILES:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return f.read().strip()
    print("Uwaga: brak psi-key.txt w static/ ani public/ — test bez klucza, Google może odmówić (błąd 429).")
    return ""


def run(url, key, strategy):
    params = [("url", url), ("strategy", strategy)] + [("category", c) for c in CATEGORIES]
    if key:
        params.append(("key", key))
    # klucz jest ograniczony do strony PMCC (Websites), więc skrypt przedstawia się jako ta strona
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"Referer": url})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Google zwrócił błąd {e.code} ({strategy}). Nic nie zapisano.")
    except urllib.error.URLError as e:
        sys.exit(f"Brak połączenia z Google ({strategy}): {e.reason}. Nic nie zapisano.")

    lh = data["lighthouseResult"]
    result = {"scores": {}, "metrics": {}}
    for c in CATEGORIES:
        result["scores"][c] = round(lh["categories"][c]["score"] * 100)
    for m in METRICS:
        a = lh["audits"].get(m)
        if a:
            result["metrics"][m] = {"value": a.get("displayValue", ""), "score": round((a.get("score") or 0) * 100)}
    return result


def to_yaml(now, url, results):
    lines = [
        "# Wyniki testu Google PageSpeed Insights dla strony /statystyki.",
        "# Plik generuje skrypt: python scripts/pagespeed-test.py — nie edytować ręcznie.",
        f'date : "{now:%Y-%m-%d}"',
        f'time : "{now:%H:%M}"',
        f'url  : "{url}"',
    ]
    for strategy, r in results.items():
        lines.append(f"{strategy}:")
        lines.append("  scores:")
        for c, v in r["scores"].items():
            lines.append(f"    {c}: {v}")
        lines.append("  metrics:")
        for m, v in r["metrics"].items():
            lines.append(f"    {m}:")
            lines.append(f'      value: "{v["value"]}"')
            lines.append(f'      score: {v["score"]}')
    return "\n".join(lines) + "\n"


def main():
    url = read_url()
    key = read_key()
    results = {}
    for strategy, label in [("mobile", "telefon"), ("desktop", "komputer")]:
        print(f"Test: {url} — {label} (ok. 30 s)…")
        results[strategy] = run(url, key, strategy)
        s = results[strategy]["scores"]
        print(f"  szybkość {s['performance']}, SEO {s['seo']}, dostępność {s['accessibility']}, dobre praktyki {s['best-practices']}")

    now = datetime.now()
    with open(OUT_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(to_yaml(now, url, results))
    print(f"Zapisano: {OUT_FILE} ({now:%d.%m.%Y %H:%M})")


if __name__ == "__main__":
    main()
