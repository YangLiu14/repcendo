#!/usr/bin/env python3
"""Install a pre-push guard that survives checking out older commits."""
from pathlib import Path
import shutil
import subprocess


def main():
    root = Path(__file__).resolve().parents[1]
    common = Path(subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        text=True,
    ).strip())
    configured = subprocess.run(
        ["git", "-C", str(root), "config", "--get", "core.hooksPath"],
        capture_output=True, text=True,
    )
    if configured.returncode not in (0, 1):
        raise SystemExit("Could not inspect Git hook configuration")
    if configured.returncode == 0:
        raise SystemExit("A custom core.hooksPath is configured; integrate the guard there before installing.")
    hook = common / "hooks/pre-push"
    marker = b"# Repcendo private-asset guard"
    if hook.exists() and marker not in hook.read_bytes():
        raise SystemExit("Existing pre-push hook preserved; integrate the guard instead of overwriting it.")
    # Keeping these in the common Git directory prevents an older checkout from
    # silently disabling the guard by removing its versioned scripts.
    for filename in ("check_private_assets.py", "private_asset_blobs.txt"):
        shutil.copyfile(root / "Scripts" / filename, common / filename)
    hook.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / ".githooks/pre-push", hook)
    hook.chmod(0o755)
    print("Installed private-asset pre-push guard:", hook)


if __name__ == "__main__":
    main()
