#!/usr/bin/env python3
"""Offline structural smoke test for the repository's two plugin marketplaces."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def read_json(relative):
    path = ROOT / relative
    assert path.is_file(), f"Missing file: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    plugin_rel = Path("plugins/repo-hygiene")
    plugin = ROOT / plugin_rel
    skill = plugin / "skills/repo-hygiene/SKILL.md"
    assert skill.is_file(), "Missing shared SKILL.md"
    frontmatter = skill.read_text(encoding="utf-8").split("---", 2)
    assert len(frontmatter) >= 3 and "name: repo-hygiene" in frontmatter[1]
    assert "description:" in frontmatter[1]
    assert (plugin / "skills/repo-hygiene/references/audit-rubric.md").exists()
    assert (plugin / "skills/repo-hygiene/assets/findings-template.md").exists()

    claude = read_json(".claude-plugin/marketplace.json")
    codex = read_json(".agents/plugins/marketplace.json")
    assert claude["name"] == codex["name"] == "repo-hygiene-marketplace"
    assert len(claude["plugins"]) == len(codex["plugins"]) == 1
    cp = claude["plugins"][0]
    xp = codex["plugins"][0]
    assert cp["name"] == xp["name"] == "repo-hygiene"
    assert cp["source"] == "./plugins/repo-hygiene"
    assert xp["source"]["source"] == "local"
    assert xp["source"]["path"] == "./plugins/repo-hygiene"
    assert xp["policy"]["installation"] == "AVAILABLE"
    assert xp["category"]
    for entry in (cp["source"], xp["source"]["path"]):
        assert not any(p == ".." for p in Path(entry).parts), "Unsafe plugin path"
        assert (ROOT / entry).resolve() == plugin.resolve()
    cmanifest = read_json("plugins/repo-hygiene/.claude-plugin/plugin.json")
    pmanifest = read_json("plugins/repo-hygiene/plugin.json")
    assert cmanifest["name"] == pmanifest["name"] == cp["name"]
    assert cmanifest["version"] == pmanifest["version"] == "1.0.0"
    assert pmanifest["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert cmanifest["license"] == pmanifest["license"] == "MIT"
    assert (ROOT / "LICENSE").is_file()
    print("PASS: marketplace catalogs, manifest identities, skill files and paths")
    print("NOTE: authoritative Claude Code/Codex plugin validation and runtime evaluation still required")


if __name__ == "__main__":
    main()
