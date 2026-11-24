#!/usr/bin/env python3
"""Fetch openapi.json from the live API and sync it to all locations.

Polls until the live spec differs from the current local copy (or until
timeout), so it always captures the freshly-deployed version.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
API_URL = "https://portalu-production.up.railway.app/openapi.json"
LOCAL = ROOT / "openapi.json"
POLL_INTERVAL = 15   # seconds between attempts
TIMEOUT = 600        # give up after 10 minutes


def fetch():
    with urllib.request.urlopen(API_URL, timeout=15) as resp:
        return json.loads(resp.read())


def current_version():
    try:
        return json.loads(LOCAL.read_text())["info"]["version"]
    except Exception:
        return None


before = current_version()
deadline = time.time() + TIMEOUT

print(f"waiting for Railway to deploy (current local: {before}) ...")

while True:
    try:
        spec = fetch()
    except Exception as e:
        print(f"  fetch error: {e}")
        spec = None

    if spec and spec["info"]["version"] != before:
        break

    if time.time() >= deadline:
        print("timeout — writing whatever is live now")
        if spec is None:
            sys.exit(1)
        break

    time.sleep(POLL_INTERVAL)

print(f"live version: {spec['info']['version']}")

targets = [
    ROOT / "openapi.json",
    ROOT / "docs" / "openapi.json",
    ROOT / "docs" / "public" / "openapi.json",
]

for target in targets:
    target.write_text(json.dumps(spec, indent=2) + "\n")
    print(f"updated {target.relative_to(ROOT)}")
