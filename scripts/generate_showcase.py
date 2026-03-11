"""
Generate showcase cache files for 6 companies (2 BR, 2 FR, 2 US).
Scrapes real data from company websites and generates bilingual DNA + Market Intel.
No synthetic/fake data generated.

Usage: GROQ_API_KEY=... python scripts/generate_showcase.py
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.intelligence import phase_discovery, phase_company_dna, phase_market_intel

COMPANIES = {
    "nubank": "nubank.com.br",
    "stone": "stone.co",
    "criteo": "criteo.com",
    "ovhcloud": "ovhcloud.com",
    "datadog": "datadoghq.com",
    "hubspot": "hubspot.com",
}

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("ERROR: Set GROQ_API_KEY environment variable")
    sys.exit(1)

cache_dir = Path(__file__).parent.parent / "data" / "cache"
cache_dir.mkdir(parents=True, exist_ok=True)

for name, url in COMPANIES.items():
    print(f"\n{'='*60}")
    print(f"Processing: {name} ({url})")
    print(f"{'='*60}")

    try:
        # Phase 1: Discovery
        print("  Phase 1: Discovery...")
        discovery = phase_discovery(url)
        print(f"  -> {discovery['pages_found']} pages found")

        if not discovery["content"]:
            print(f"  ERROR: Could not scrape {url}")
            continue

        # Phase 2: Company DNA (both languages)
        print("  Phase 2: Company DNA (EN)...")
        dna_en = phase_company_dna(discovery["content"], url, api_key,
                                   meta=discovery.get("meta"), lang="en")
        print(f"  -> {dna_en.get('company_name', 'OK')}")

        print("  Phase 2: Company DNA (PT)...")
        dna_pt = phase_company_dna(discovery["content"], url, api_key,
                                   meta=discovery.get("meta"), lang="pt")
        print(f"  -> {dna_pt.get('company_name', 'OK')}")

        # Phase 3: Market Intel (both languages)
        print("  Phase 3: Market Intel (EN)...")
        market_en = phase_market_intel(dna_en, discovery["content"], api_key, lang="en")
        print(f"  -> {len(market_en.get('likely_competitors', []))} competitors")

        print("  Phase 3: Market Intel (PT)...")
        market_pt = phase_market_intel(dna_pt, discovery["content"], api_key, lang="pt")
        print(f"  -> {len(market_pt.get('likely_competitors', []))} competitors")

        # Build cache file
        cache_data = {
            "url": url,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "pages_scraped": discovery["urls"],
            "meta": discovery.get("meta", {}),
            "dna": {
                "pt": dna_pt,
                "en": dna_en,
            },
            "market": {
                "pt": market_pt,
                "en": market_en,
            },
        }

        out_path = cache_dir / f"{name}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        print(f"  Saved: {out_path}")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\nDone!")
