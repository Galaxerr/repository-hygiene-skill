#!/usr/bin/env python3
"""Validate this repository's shared skill and marketplace packages offline."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import yaml
from markdown_it import MarkdownIt


ROOT = Path(__file__).resolve().parents[1]
NAME = "repo-hygiene"
MARKETPLACE = "repo-hygiene-marketplace"
REPOSITORY = "https://github.com/Galaxerr/repository-hygiene-skill"
PLUGIN = Path("plugins") / NAME
SKILL_DIR = PLUGIN / "skills" / NAME
SKILL = SKILL_DIR / "SKILL.md"
RESOURCES = {"references/audit-rubric.md", "assets/findings-template.md"}
NUMERIC = r"(?:0|[1-9][0-9]*)"
PRERELEASE = rf"(?:{NUMERIC}|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
BUILD = r"[0-9A-Za-z-]+"
SEMVER = re.compile(
    rf"{NUMERIC}\.{NUMERIC}\.{NUMERIC}"
    rf"(?:-{PRERELEASE}(?:\.{PRERELEASE})*)?(?:\+{BUILD}(?:\.{BUILD})*)?"
)


class ValidationError(ValueError):
    pass


def require(condition, location, message):
    if not condition:
        raise ValidationError(f"{location}: {message}")


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def mapping(value, location):
    require(isinstance(value, dict), location, "expected a mapping")
    return value


def read_text(path, tracked, within=Path(".")):
    try:
        return tracked_file(path, tracked, within).read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError(f"{path}: expected UTF-8: {error}") from error


def read_mapping(path, contents, parse, format_name):
    try:
        value = parse(contents)
    except (ValueError, LookupError, yaml.YAMLError) as error:
        raise ValidationError(f"{path}: invalid {format_name}: {error}") from error
    return mapping(value, path)


def tracked_files():
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True)
    require(result.returncode == 0, ROOT, os.fsdecode(result.stderr).strip())
    return {Path(path) for path in os.fsdecode(result.stdout).split("\0") if path}


def tracked_file(relative, tracked, within=Path(".")):
    path = ROOT / relative
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError, ValueError) as error:
        raise ValidationError(f"{relative}: cannot resolve path: {error}") from error
    require(resolved.is_relative_to(ROOT / within), relative, f"path escapes {within}")
    require(path.is_file(), relative, "missing file")
    require(relative in tracked and resolved.relative_to(ROOT) in tracked,
            relative, "file and resolved target must be tracked by Git")
    if path.is_symlink():
        target = path.readlink()
        require(not target.is_absolute() and ".." not in target.parts, relative,
                "symlink target must stay at or below its containing directory")
        require(relative.parent / target in tracked, relative,
                "direct symlink target must be tracked by Git")
    return path


def invalid_constant(value):
    raise ValueError(f"non-JSON constant {value}")


def read_json(relative, tracked):
    return read_mapping(relative, read_text(relative, tracked),
                        lambda text: json.loads(text, parse_constant=invalid_constant), "JSON")


def validate_catalog(path, tracked, *, codex):
    catalog = read_json(path, tracked)
    require(catalog.get("name") == MARKETPLACE, f"{path}: name", f"expected {MARKETPLACE}")
    entries = catalog.get("plugins")
    require(isinstance(entries, list) and len(entries) == 1, f"{path}: plugins",
            "expected exactly one plugin")
    entry = mapping(entries[0], f"{path}: plugins[0]")
    require(entry.get("name") == NAME, f"{path}: plugins[0].name", f"expected {NAME}")
    source = entry.get("source")
    if codex:
        source = mapping(source, f"{path}: plugins[0].source")
        require(source.get("source") == "local", f"{path}: plugins[0].source.source",
                "expected local")
        source = source.get("path")
        policy = mapping(entry.get("policy"), f"{path}: plugins[0].policy")
        for field, expected in (("installation", "AVAILABLE"), ("authentication", "ON_INSTALL")):
            require(policy.get(field) == expected, f"{path}: plugins[0].policy.{field}",
                    f"expected {expected}")
        require(nonempty(entry.get("category")), f"{path}: plugins[0].category",
                "expected a nonempty string")
    else:
        owner = mapping(catalog.get("owner"), f"{path}: owner")
        require(owner.get("name") == "Galaxerr", f"{path}: owner.name", "expected Galaxerr")
        extra = entry.keys() - {"name", "source"}
        require(not extra, f"{path}: plugins[0]",
                f"use the Claude manifest for plugin metadata: {', '.join(sorted(extra))}")
    require(nonempty(source) and source.startswith("./") and ".." not in Path(source).parts
            and Path(source) == PLUGIN, f"{path}: plugins[0].source",
            f"expected a contained local path to ./{PLUGIN}")
    require((ROOT / source).resolve() == ROOT / PLUGIN, f"{path}: plugins[0].source",
            f"must resolve to ./{PLUGIN} without redirection")


def validate_manifests(tracked):
    claude = PLUGIN / ".claude-plugin/plugin.json"
    portable = PLUGIN / "plugin.json"
    manifests = {}
    for path in (claude, portable):
        manifest = manifests[path] = read_json(path, tracked)
        expected = {"name": NAME, "repository": REPOSITORY, "homepage": REPOSITORY, "license": "MIT"}
        for field, value in expected.items():
            require(manifest.get(field) == value, f"{path}: {field}", f"expected {value}")
        version = manifest.get("version")
        require(isinstance(version, str) and SEMVER.fullmatch(version), f"{path}: version",
                "expected a semantic version such as 1.0.0")
        require(nonempty(manifest.get("description")), f"{path}: description",
                "expected a nonempty string")
        # This instruction-only package uses standard discovery without manifest components.
        metadata = set(expected) | {"version", "description", "author", "keywords"}
        metadata.add("displayName" if path == claude else "$schema")
        extra = manifest.keys() - metadata
        require(not extra, path, f"unexpected manifest fields: {', '.join(sorted(extra))}")
        if "author" in manifest:
            author = mapping(manifest["author"], f"{path}: author")
            require(all(isinstance(value, str) for value in author.values()), f"{path}: author",
                    "expected string values")
        if "keywords" in manifest:
            keywords = manifest["keywords"]
            require(isinstance(keywords, list) and all(nonempty(word) for word in keywords),
                    f"{path}: keywords", "expected a list of nonempty strings")
        if "displayName" in manifest:
            require(nonempty(manifest["displayName"]), f"{path}: displayName",
                    "expected a nonempty string")
    require(manifests[portable].get("$schema") ==
            "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            f"{portable}: $schema", "expected the portable Agent Plugins 1.0.0 schema")
    require(manifests[portable]["version"] == manifests[claude]["version"],
            f"{portable}: version", f"must match {claude}")


def validate_skill(tracked):
    text = read_text(SKILL, tracked, SKILL_DIR)
    parts = re.split(r"^---[ \t]*$", text, maxsplit=2, flags=re.MULTILINE)
    require(len(parts) == 3 and not parts[0], SKILL, "expected YAML frontmatter at the start")
    _, header, body = parts
    frontmatter = read_mapping(SKILL, header, yaml.safe_load, "YAML")
    require(frontmatter.get("name") == SKILL_DIR.name, f"{SKILL}: name",
            f"expected {SKILL_DIR.name}")
    require(nonempty(body), SKILL, "missing Markdown instructions after frontmatter")
    for field, limit in (("description", 1024), ("compatibility", 500)):
        if field == "description" or field in frontmatter:
            value = frontmatter.get(field)
            require(nonempty(value) and len(value) <= limit, f"{SKILL}: {field}",
                    f"expected a nonempty string of at most {limit} characters")
    for field in ("license", "allowed-tools"):
        if field in frontmatter:
            require(nonempty(frontmatter[field]), f"{SKILL}: {field}", "expected a nonempty string")
    if "metadata" in frontmatter:
        metadata = mapping(frontmatter["metadata"], f"{SKILL}: metadata")
        require(all(isinstance(key, str) and isinstance(value, str)
                    for key, value in metadata.items()), f"{SKILL}: metadata",
                "expected string keys and values")

    validate_resource_links(body, tracked)

    presentation = SKILL_DIR / "agents/openai.yaml"
    if presentation in tracked or (ROOT / presentation).exists():
        contents = read_text(presentation, tracked, SKILL_DIR)
        metadata = read_mapping(presentation, contents, yaml.safe_load, "YAML")
        require(metadata.keys() <= {"interface"}, presentation, "expected presentation metadata only")
        if "interface" in metadata:
            interface = mapping(metadata["interface"], f"{presentation}: interface")
            require(all(nonempty(value) for value in interface.values()), f"{presentation}: interface",
                    "expected nonempty string fields")
            for field in ("icon_small", "icon_large"):
                if field in interface:
                    validate_skill_path(interface[field], tracked, f"{presentation}: interface.{field}")


def validate_skill_path(target, tracked, location):
    path = Path(target)
    require(not path.is_absolute() and ".." not in path.parts
            and ":" not in target and "\\" not in target,
            location, f"resource link must stay inside the skill directory: {target}")
    tracked_file(SKILL_DIR / path, tracked, SKILL_DIR)


def validate_resource_links(body, tracked):
    markdown = MarkdownIt("commonmark")
    # Inspect every parsed destination locally without rendering or following links.
    markdown.validateLink = lambda _: True
    links = [
        child.attrGet("href" if child.type == "link_open" else "src")
        for token in markdown.parse(body)
        for child in token.children or ()
        if child.type in {"link_open", "image"}
    ]
    resources = set()
    for link in links:
        try:
            url = urlsplit(link)
        except ValueError as error:
            raise ValidationError(f"{SKILL}: invalid resource link {link!r}: {error}") from error
        if url.scheme in {"https", "http"}:
            continue
        target = unquote(url.path)
        require(not url.scheme and not url.netloc,
                SKILL, f"resource link must stay inside the skill directory: {link}")
        if target:
            validate_skill_path(target, tracked, SKILL)
            resources.add(Path(target).as_posix())
    require(RESOURCES <= resources, SKILL,
            f"missing resource links: {', '.join(sorted(RESOURCES - resources))}")

def main():
    tracked = tracked_files()
    root_license = tracked_file(Path("LICENSE"), tracked)
    license_path = SKILL_DIR / "LICENSE"
    skill_license = tracked_file(license_path, tracked, SKILL_DIR)
    require(skill_license.read_bytes() == root_license.read_bytes(), license_path,
            "must match the root LICENSE")
    unsupported_components = {
        ".codex-plugin", ".mcp.json", "mcp.json", ".app.json", "agents", "commands", "hooks",
    }
    for path in sorted(tracked):
        require(path.name != "SKILL.md" or path == SKILL, path, f"duplicate skill; use {SKILL}")
        if path.is_relative_to(PLUGIN):
            require(path.relative_to(PLUGIN).parts[0] not in unsupported_components,
                    path, "unexpected component in the shared skill package")
            tracked_file(path, tracked, SKILL_DIR if path.is_relative_to(SKILL_DIR) else PLUGIN)
    validate_catalog(Path(".claude-plugin/marketplace.json"), tracked, codex=False)
    validate_catalog(Path(".agents/plugins/marketplace.json"), tracked, codex=True)
    validate_manifests(tracked)
    validate_skill(tracked)
    print("PASS: marketplace catalogs, plugin manifests, and shared skill integrity")


if __name__ == "__main__":
    try:
        main()
    except (ValidationError, OSError) as error:
        sys.exit(f"FAIL: {error}")
