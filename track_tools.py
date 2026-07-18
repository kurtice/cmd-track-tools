#!/usr/bin/env python3
"""
track_tools.py — Maintain a single-file Markdown inventory of CLI tools
installed via common package managers (Homebrew, pipx, pip3 global, npm
global, cargo).

Run it any time. It:
  - Detects which package managers are present on this machine.
  - Diffs the currently-installed tool list for each manager against
    what's already recorded in TOOLS.md.
  - Adds newly-installed tools as active entries (dated "since").
  - Marks tools that have disappeared with strikethrough + "removed" date,
    instead of deleting them, so history is preserved.
  - Un-strikes a tool if it was removed before and has since been
    reinstalled.

Usage:
    python3 track_tools.py                # updates ./TOOLS.md
    python3 track_tools.py --file PATH     # updates a custom path
"""

import argparse
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

TODAY = date.today().isoformat()

# Order matters: this is the order sections appear in the file.
SOURCES = ["Homebrew", "pipx", "pip3 (global)", "npm (global)", "cargo"]

ACTIVE_RE = re.compile(r"^- (?!~~)(\S+) _\(since (\d{4}-\d{2}-\d{2})\)_\s*$")
REMOVED_RE = re.compile(r"^- ~~(\S+)~~ _\(removed (\d{4}-\d{2}-\d{2})\)_\s*$")


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return ""


def get_brew():
    if not shutil.which("brew"):
        return None
    out = run(["brew", "leaves"])
    return sorted(set(out.split()))


def get_pipx():
    if not shutil.which("pipx"):
        return None
    out = run(["pipx", "list", "--short"])
    names = [line.split()[0] for line in out.splitlines() if line.strip()]
    return sorted(set(names))


def get_pip3_global():
    if not shutil.which("pip3"):
        return None
    out = run(["pip3", "list", "--not-required", "--format=freeze"])
    names = []
    for line in out.splitlines():
        if "==" in line:
            names.append(line.split("==")[0])
    return sorted(set(names))


def get_npm_global():
    if not shutil.which("npm"):
        return None
    out = run(["npm", "ls", "-g", "--depth=0", "--json"])
    try:
        data = json.loads(out)
        deps = data.get("dependencies", {})
        return sorted(deps.keys())
    except Exception:
        return []


def get_cargo():
    if not shutil.which("cargo"):
        return None
    out = run(["cargo", "install", "--list"])
    names = []
    for line in out.splitlines():
        if line and not line.startswith(" ") and " v" in line:
            names.append(line.split(" v")[0].strip())
    return sorted(set(names))


GETTERS = {
    "Homebrew": get_brew,
    "pipx": get_pipx,
    "pip3 (global)": get_pip3_global,
    "npm (global)": get_npm_global,
    "cargo": get_cargo,
}


def parse_existing(text):
    """Return {section_name: {tool_name: (state, date)}}"""
    sections = {}
    current = None
    for line in text.splitlines():
        header = re.match(r"^## (.+)$", line)
        if header:
            current = header.group(1).strip()
            sections[current] = {}
            continue
        if current is None:
            continue
        m = ACTIVE_RE.match(line)
        if m:
            sections[current][m.group(1)] = ("active", m.group(2))
            continue
        m = REMOVED_RE.match(line)
        if m:
            sections[current][m.group(1)] = ("removed", m.group(2))
            continue
    return sections


def merge(existing, current_list):
    """existing: {name: (state, date)}; current_list: list[str] or None.
    Returns updated {name: (state, date)} for this section."""
    if current_list is None:
        # package manager not present on this run — leave section untouched
        return existing

    updated = dict(existing)
    current_set = set(current_list)

    for name in current_set:
        prev = updated.get(name)
        if prev is None:
            updated[name] = ("active", TODAY)
        elif prev[0] == "removed":
            # reinstalled after being marked removed
            updated[name] = ("active", TODAY)
        # else: already active, keep original since-date

    for name, (state, d) in list(updated.items()):
        if name not in current_set and state == "active":
            updated[name] = ("removed", TODAY)

    return updated


def render(all_sections):
    lines = ["# Tools Inventory", "", f"_Last updated: {TODAY}_", ""]
    for source in SOURCES:
        entries = all_sections.get(source, {})
        lines.append(f"## {source}")
        if not entries:
            lines.append("_(none recorded)_")
            lines.append("")
            continue
        for name in sorted(entries.keys(), key=str.lower):
            state, d = entries[name]
            if state == "active":
                lines.append(f"- {name} _(since {d})_")
            else:
                lines.append(f"- ~~{name}~~ _(removed {d})_")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="TOOLS.md")
    args = parser.parse_args()

    path = Path(args.file)
    existing_text = path.read_text() if path.exists() else ""
    existing_sections = parse_existing(existing_text)

    all_sections = {}
    for source in SOURCES:
        current_list = GETTERS[source]()
        prev = existing_sections.get(source, {})
        all_sections[source] = merge(prev, current_list)

    path.write_text(render(all_sections))
    print(f"Updated {path.resolve()}")


if __name__ == "__main__":
    main()
