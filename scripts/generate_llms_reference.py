#!/usr/bin/env python3
"""
Regenerates the ## API Reference section of llms.txt from api-design.yaml.
Everything above ## API Reference is preserved unchanged — that content is
hand-written and only updated when product decisions change.

Usage:
    python scripts/generate_llms_reference.py
"""

import sys
import yaml
from pathlib import Path

SPEC_FILE = Path("api-design.yaml")
LLMS_FILE = Path("llms.txt")
BASE_URL = "https://portalu.readme.io/reference"
SECTION_MARKER = "## API Reference"


def load_spec(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def get_operations_by_tag(spec: dict) -> dict[str, list[dict]]:
    # Preserve tag order as defined in the spec
    tag_order = [tag["name"] for tag in spec.get("tags", [])]
    groups: dict[str, list[dict]] = {tag: [] for tag in tag_order}

    for path_item in spec.get("paths", {}).values():
        for method in ["get", "post", "put", "patch", "delete"]:
            op = path_item.get(method)
            if not op or not op.get("operationId"):
                continue
            tag = (op.get("tags") or ["Other"])[0]
            if tag not in groups:
                groups[tag] = []
            groups[tag].append({
                "operationId": op["operationId"],
                "summary": op.get("summary", ""),
                "description": op.get("description", ""),
                "permissions": op.get("x-required-permissions", []),
            })

    return groups


def build_inline_description(op: dict) -> str:
    parts = []

    # First line of description, only if it adds context beyond the summary
    # and isn't just restating the permission requirement (already captured below)
    raw_desc = (op["description"] or "").strip()
    if raw_desc:
        first_line = raw_desc.splitlines()[0].strip().rstrip(".")
        is_redundant = (
            not first_line
            or first_line.lower() == op["summary"].lower().rstrip(".")
            or first_line.lower().startswith("requires ")
        )
        if not is_redundant:
            parts.append(first_line)

    # Required permissions (sourced from x-required-permissions, not description prose)
    perms = op["permissions"]
    if perms:
        joined = "` or `".join(perms)
        parts.append(f"Requires `{joined}`")

    return ". ".join(parts)


def generate_reference_section(groups: dict[str, list[dict]]) -> str:
    lines = [
        SECTION_MARKER,
        "",
        "Append `.md` to any documentation page URL to get its markdown version.",
        "",
    ]

    for tag, ops in groups.items():
        if not ops:
            continue
        lines.append(f"### {tag}")
        lines.append("")
        for op in ops:
            url = f"{BASE_URL}/{op['operationId'].lower()}.md"
            desc = build_inline_description(op)
            suffix = f": {desc}." if desc else ""
            lines.append(f"- [{op['summary']}]({url}){suffix}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def update_llms(llms_path: Path, new_section: str) -> bool:
    content = llms_path.read_text()

    idx = content.find(f"\n{SECTION_MARKER}")
    if idx != -1:
        preamble = content[: idx + 1]  # include the preceding newline
    else:
        idx = content.find(SECTION_MARKER)
        if idx == -1:
            print(f"ERROR: '{SECTION_MARKER}' not found in {llms_path}", file=sys.stderr)
            sys.exit(1)
        preamble = content[:idx]

    updated = preamble + new_section
    if updated == content:
        print("llms.txt is already up to date.")
        return False

    llms_path.write_text(updated)
    print("llms.txt updated.")
    return True


def main():
    for path in [SPEC_FILE, LLMS_FILE]:
        if not path.exists():
            print(f"ERROR: {path} not found. Run from the repo root.", file=sys.stderr)
            sys.exit(1)

    spec = load_spec(SPEC_FILE)
    groups = get_operations_by_tag(spec)
    new_section = generate_reference_section(groups)
    update_llms(LLMS_FILE, new_section)


if __name__ == "__main__":
    main()
