#!/usr/bin/env python3
"""Fetch openapi.json from the live API and sync it to all locations."""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
API_URL = "https://portalu-production.up.railway.app/openapi.json"

print(f"fetching {API_URL} ...")
try:
    with urllib.request.urlopen(API_URL, timeout=15) as resp:
        spec = json.loads(resp.read())
except Exception as e:
    print(f"error: {e}")
    sys.exit(1)

targets = [
    ROOT / "openapi.json",
    ROOT / "docs" / "openapi.json",
    ROOT / "docs" / "public" / "openapi.json",
]

for target in targets:
    target.write_text(json.dumps(spec, indent=2) + "\n")
    print(f"updated {target.relative_to(ROOT)}")
