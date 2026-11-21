"""Capture observable state of a disposable fixture as JSON on stdout."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess


def snapshot(root, before):
    git_dir = root / ".git"
    config = git_dir / "config"
    if (
        git_dir.is_symlink()
        or not git_dir.is_dir()
        or config.is_symlink()
        or not config.is_file()
        or os.path.lexists(git_dir / "commondir")
        or os.path.lexists(git_dir / "config.worktree")
    ):
        raise SystemExit("Expected the standalone Git directory produced by prepare.sh.")
    config_hash = hashlib.sha256(config.read_bytes()).hexdigest()
    if before is not None and config_hash != before["git_config_sha256"]:
        raise SystemExit("Fixture Git configuration changed. Capture stopped before running Git.")

    git_env = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    git_env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_ATTR_NOSYSTEM="1")

    def git(*args):
        return subprocess.check_output(
            ["git", "--no-pager", "--no-optional-locks", "-C", str(root), *args],
            env=git_env,
        ).decode("utf-8", errors="surrogateescape")

    if Path(git("rev-parse", "--show-toplevel").rstrip("\n")).resolve() != root:
        raise SystemExit("Pass the root of the disposable fixture repository.")

    files = {}
    for directory, dirs, names in os.walk(root, onerror=_raise_walk_error):
        path = Path(directory)
        if path == root:
            dirs[:] = [name for name in dirs if name != ".git"]
            names = [name for name in names if name != ".git"]
        for name in dirs + names:
            entry = path / name
            mode = entry.lstat().st_mode
            record = {"mode": oct(mode)}
            if stat.S_ISLNK(mode):
                record["target"] = os.readlink(entry)
            elif stat.S_ISREG(mode):
                record["sha256"] = hashlib.sha256(entry.read_bytes()).hexdigest()
            files[entry.relative_to(root).as_posix()] = record

    diff_flags = ("--binary", "--no-ext-diff", "--no-textconv", "--no-color")
    return {
        "head": git("rev-parse", "HEAD"),
        "head_ref": git("rev-parse", "--symbolic-full-name", "HEAD"),
        "refs": git("for-each-ref", "--format=%(refname) %(objectname)"),
        "remotes": git("remote", "-v"),
        "git_config_sha256": config_hash,
        "status": git("status", "--porcelain=v1", "--untracked-files=all"),
        "worktree_diff": git("diff", *diff_flags),
        "index_diff": git("diff", "--cached", *diff_flags),
        "index_entries": git("ls-files", "--stage", "-v"),
        "files": files,
    }


def _raise_walk_error(error):
    raise error


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--before", type=Path, help="baseline snapshot for a post-session capture")
    args = parser.parse_args()
    before = json.loads(args.before.read_text(encoding="utf-8")) if args.before else None
    print(json.dumps(snapshot(args.fixture.resolve(), before), indent=2, sort_keys=True))
