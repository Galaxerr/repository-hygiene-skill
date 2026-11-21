"""Exercise the package validator against disposable Git checkouts."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLAUDE = Path(".claude-plugin/marketplace.json")
CODEX = Path(".agents/plugins/marketplace.json")
PLUGIN = Path("plugins/repo-hygiene")
MANIFEST = PLUGIN / "plugin.json"
CLAUDE_MANIFEST = PLUGIN / ".claude-plugin/plugin.json"
SKILL = PLUGIN / "skills/repo-hygiene/SKILL.md"
PACKAGED_LICENSE = SKILL.parent / "LICENSE"
RUBRIC = SKILL.parent / "references/audit-rubric.md"
PRESENTATION = SKILL.parent / "agents/openai.yaml"
VALIDATOR = Path("tests/validate_package.py")


def git(root, *args):
    return subprocess.check_output(["git", "-C", root, *args])


class PackageValidationTest(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.checkout = Path(temp.name) / "checkout"
        self.checkout.mkdir()
        inputs = git(ROOT, "ls-files", "-z", "--", CLAUDE, CODEX, PLUGIN, "LICENSE")
        for path in [*map(Path, os.fsdecode(inputs).rstrip("\0").split("\0")), VALIDATOR]:
            dest = self.checkout / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, dest, follow_symlinks=False)
        git(self.checkout, "init", "-q")
        git(self.checkout, "add", "--all")

    def validate(self, error=None):
        for flags in ([], ["-O"]):
            with self.subTest(flags=flags):
                result = subprocess.run(
                    [sys.executable, *flags, VALIDATOR],
                    cwd=self.checkout,
                    capture_output=True,
                    text=True,
                )
                if error is None:
                    self.assertEqual(result.returncode, 0, result.stderr)
                else:
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn(error, result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def update_json(self, path, update):
        path = self.checkout / path
        value = json.loads(path.read_text(encoding="utf-8"))
        update(value)
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_valid_tree(self):
        self.validate()

    def test_packaged_license_matches_root_notice(self):
        (self.checkout / PACKAGED_LICENSE).write_text("MIT\n", encoding="utf-8")
        self.validate(f"{PACKAGED_LICENSE}: must match the root LICENSE")

    def test_missing_packaged_license(self):
        (self.checkout / PACKAGED_LICENSE).unlink()
        self.validate(f"{PACKAGED_LICENSE}: missing file")

    def test_matching_new_versions(self):
        for path in (CLAUDE_MANIFEST, MANIFEST):
            self.update_json(path, lambda manifest: manifest.update(version="1.1.0"))
        self.validate()

    def test_malformed_catalog_json(self):
        (self.checkout / CODEX).write_text("{", encoding="utf-8")
        self.validate(f"{CODEX}: invalid JSON")

    def test_non_json_constant(self):
        self.update_json(CODEX, lambda catalog: catalog.update(note=float("nan")))
        self.validate(f"{CODEX}: invalid JSON")

    def test_catalog_invalid_utf8(self):
        (self.checkout / CODEX).write_bytes(b"\xff")
        self.validate(f"{CODEX}: expected UTF-8")

    def test_malformed_skill_frontmatter(self):
        (self.checkout / SKILL).write_text(
            "---\nname: repo-hygiene\ndescription: [unclosed\n---\nInstructions\n",
            encoding="utf-8",
        )
        self.validate(f"{SKILL}: invalid YAML")

    def test_misplaced_skill_frontmatter(self):
        skill = self.checkout / SKILL
        skill.write_text("Before frontmatter\n" + skill.read_text(encoding="utf-8"), encoding="utf-8")
        self.validate(f"{SKILL}: expected YAML frontmatter at the start")

    def test_invalid_optional_frontmatter(self):
        skill = self.checkout / SKILL
        contents = skill.read_text(encoding="utf-8").replace("license: MIT", "metadata: {version: 1}")
        skill.write_text(contents, encoding="utf-8")
        self.validate(f"{SKILL}: metadata")

    def test_invalid_yaml_date(self):
        skill = self.checkout / SKILL
        contents = skill.read_text(encoding="utf-8").replace(
            "license: MIT", "metadata: {date: 2026-13-01}"
        )
        skill.write_text(contents, encoding="utf-8")
        self.validate(f"{SKILL}: invalid YAML")

    def test_invalid_yaml_tagged_scalar(self):
        skill = self.checkout / SKILL
        contents = skill.read_text(encoding="utf-8").replace(
            "license: MIT", "metadata: {version: !!int ''}"
        )
        skill.write_text(contents, encoding="utf-8")
        self.validate(f"{SKILL}: invalid YAML")

    def test_missing_catalog(self):
        (self.checkout / CLAUDE).unlink()
        self.validate(f"{CLAUDE}: missing file")

    def test_missing_resource(self):
        (self.checkout / RUBRIC).unlink()
        self.validate(f"{RUBRIC}: missing file")

    def test_untracked_resource(self):
        git(self.checkout, "rm", "--cached", "--", RUBRIC)
        self.validate(f"{RUBRIC}: file and resolved target must be tracked by Git")

    def test_missing_policy(self):
        self.update_json(CODEX, lambda catalog: catalog["plugins"][0]["policy"].pop("authentication"))
        self.validate(f"{CODEX}: plugins[0].policy.authentication")

    def test_version_drift(self):
        self.update_json(MANIFEST, lambda manifest: manifest.update(version="1.1.0"))
        self.validate(f"{MANIFEST}: version")

    def test_matching_invalid_versions(self):
        for path in (CLAUDE_MANIFEST, MANIFEST):
            self.update_json(path, lambda manifest: manifest.update(version="1.1.0-01"))
        self.validate(f"{CLAUDE_MANIFEST}: version")

    def test_manifest_identity_drift(self):
        self.update_json(MANIFEST, lambda manifest: manifest.update(name="other-skill"))
        self.validate(f"{MANIFEST}: name")

    def test_noncanonical_url(self):
        self.update_json(MANIFEST, lambda manifest: manifest.update(homepage="https://example.com"))
        self.validate(f"{MANIFEST}: homepage")

    def test_escaping_catalog_source(self):
        self.update_json(CLAUDE, lambda catalog: catalog["plugins"][0].update(source="../outside"))
        self.validate(f"{CLAUDE}: plugins[0].source")

    def test_duplicate_codex_manifest(self):
        path = PLUGIN / ".codex-plugin/plugin.json"
        overlay = self.checkout / path
        overlay.parent.mkdir()
        overlay.write_text("{}", encoding="utf-8")
        git(self.checkout, "add", "--", path)
        self.validate(f"{path}: unexpected component")

    def test_duplicate_skill(self):
        path = PLUGIN / "skills/other/SKILL.md"
        (self.checkout / path).parent.mkdir()
        shutil.copy2(self.checkout / SKILL, self.checkout / path)
        git(self.checkout, "add", "--", path)
        self.validate(f"{path}: duplicate skill")

    def test_escaping_resource_link(self):
        skill = self.checkout / SKILL
        with skill.open("a", encoding="utf-8") as contents:
            contents.write("\n[Outside](../outside.md)\n")
        self.validate(f"{SKILL}: resource link must stay inside")

    def test_escaping_reference_link(self):
        with (self.checkout / SKILL).open("a", encoding="utf-8") as contents:
            contents.write("\n[Outside][out]\n\n[out]: <%2e%2e/outside file.md>\n")
        self.validate(f"{SKILL}: resource link must stay inside")

    def test_escaping_presentation_icon(self):
        with (self.checkout / PRESENTATION).open("a", encoding="utf-8") as contents:
            contents.write('  icon_small: "../../outside.svg"\n')
        self.validate(f"{PRESENTATION}: interface.icon_small")

    def test_literal_link_example(self):
        with (self.checkout / SKILL).open("a", encoding="utf-8") as contents:
            contents.write("\n```markdown\n[Example](absent.md)\n```\n")
        self.validate()

    def test_required_link_inside_code_is_missing(self):
        skill = self.checkout / SKILL
        contents = skill.read_text(encoding="utf-8").replace(
            "[audit rubric](references/audit-rubric.md)", "`[audit rubric](references/audit-rubric.md)`"
        )
        skill.write_text(contents, encoding="utf-8")
        self.validate(f"{SKILL}: missing resource links")

    def test_escaping_resource_symlink(self):
        target = self.checkout.parent / "outside.md"
        target.write_text("Outside the checkout\n", encoding="utf-8")
        rubric = self.checkout / RUBRIC
        rubric.unlink()
        rubric.symlink_to(os.path.relpath(target, rubric.parent))
        git(self.checkout, "add", "--", RUBRIC)
        self.validate(f"{RUBRIC}: path escapes")

    def test_symlink_leaving_and_reentering_skill(self):
        rubric = self.checkout / RUBRIC
        target = rubric.with_name("rubric-real.md")
        rubric.rename(target)
        rubric.symlink_to(Path("../..") / SKILL.parent.name / "references" / target.name)
        git(self.checkout, "add", "--", RUBRIC, target.relative_to(self.checkout))
        self.validate(f"{RUBRIC}: symlink target must stay")


if __name__ == "__main__":
    unittest.main()
