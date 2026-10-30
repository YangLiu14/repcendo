#!/usr/bin/env python3
"""Reject private exercise assets anywhere in the history of refs being pushed."""
import argparse
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TEXT = {".md", ".json", ".html", ".js", ".css", ".csv", ".py", ".txt"}
MEDIA = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".tif", ".tiff", ".exr",
         ".mp4", ".mov", ".webm", ".blend", ".glb", ".gltf", ".fbx", ".obj",
         ".mtl", ".usd", ".usda", ".usdc", ".usdz", ".stl", ".ply"}
PRIVATE_DIR = re.compile(
    r"^docs/(?:animation-[^/]+|character-[^/]+|equipment-references|motion-references)/"
)


def git(repo, *args, data=None):
    return subprocess.check_output(["git", "-C", str(repo), *args], input=data)


def private_path(path):
    """Match local-only folders, and reject misplaced media outside UI folders."""
    suffix = PurePosixPath(path).suffix.lower()
    if path.startswith("Repcendo/Resources/ExerciseAnimations/"):
        return path != "Repcendo/Resources/ExerciseAnimations/catalog.json"
    if path.startswith("docs/screenshots/animation-"):
        return True
    if PRIVATE_DIR.match(path) or path.startswith("docs/research/deformation-evidence/"):
        return suffix not in TEXT
    if path.startswith(("build/", ".tripo/", "tripo-out/")):
        return True
    if suffix in MEDIA or re.fullmatch(r"\.blend\d+", suffix):
        return not (
            path.startswith("Repcendo/Assets.xcassets/")
            or path.startswith("docs/screenshots/")
        )
    return False


def blocked_blobs():
    # Hashes only: no private file contents are stored in the repository.
    return set((Path(__file__).with_name("private_asset_blobs.txt")).read_text().split())


def inspect_history(repo, revisions, denied):
    """Inspect every historical root tree, not just the tip or remote delta."""
    commits, trees, violations = set(), set(), set()
    for revision in revisions:
        oid = git(repo, "rev-parse", "--verify", revision + "^{}").decode().strip()
        kind = git(repo, "cat-file", "-t", oid).decode().strip()
        if kind == "commit":
            commits.add(oid)
        elif kind == "tree":
            trees.add(oid)
        else:
            violations.add("Direct blob reference: " + revision)
    if commits:
        trees.update(git(repo, "log", "--format=%T", *sorted(commits), "--").decode().split())
    for tree in sorted(trees):
        for entry in git(repo, "ls-tree", "-r", "-z", tree).split(b"\0"):
            if not entry:
                continue
            metadata, raw_path = entry.split(b"\t", 1)
            _, kind, oid = metadata.decode().split()
            # A gitlink pins the upstream repository; its contents are not pushed.
            if kind != "blob":
                continue
            path = raw_path.decode("utf-8", errors="surrogateescape")
            if private_path(path):
                violations.add("Private asset path: " + path)
            if oid in denied:
                violations.add("Previously removed asset content: " + path)
    return sorted(violations), len(trees)


def push_revisions(lines):
    revisions = []
    for line in lines:
        fields = line.split()
        if len(fields) != 4:
            raise ValueError("Malformed pre-push input")
        _, local_oid, remote_ref, _ = fields
        if set(local_oid) == {"0"}:
            continue  # Deleting a remote ref transfers no asset objects.
        if not remote_ref.startswith(("refs/heads/", "refs/tags/")):
            raise ValueError("Internal snapshots must not be pushed: " + remote_ref)
        revisions.append(local_oid)
    return revisions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--pre-push", action="store_true")
    mode.add_argument("--all", action="store_true", help="Check every local ref, including internal snapshots")
    parser.add_argument("revisions", nargs="*")
    args = parser.parse_args()
    try:
        if args.pre_push:
            revisions = push_revisions(sys.stdin)
        elif args.all:
            revisions = git(ROOT, "for-each-ref", "--format=%(refname)").decode().split()
        else:
            revisions = args.revisions or ["HEAD"]
        violations, count = inspect_history(ROOT, revisions, blocked_blobs())
        if violations:
            print("Push blocked: private exercise assets are present in reachable history.", file=sys.stderr)
            print("\n".join(violations[:12]), file=sys.stderr)
            if len(violations) > 12:
                print(f"... {len(violations)} findings total", file=sys.stderr)
            print("Remove these assets from every affected commit; deleting only the latest copy is insufficient.", file=sys.stderr)
            return 1
        print(f"Private asset check passed: {count} historical trees checked.")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("Private asset check could not complete; push blocked: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
