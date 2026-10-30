"""Reproducible local production/verification entry point for sculpture motions.

Run with a Python containing Pillow. Blender/ffmpeg/ffprobe must be on PATH.
This runner automates existing motion adapters; it does not invent new exercises.
"""
import argparse
import importlib.util
import json
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from exercise_catalog import EXERCISES

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "Scripts"
BUILD = ROOT / "build/animation-pipeline"


def stages(mode):
    def python(script):
        return [sys.executable, str(SCRIPTS / "animation_samples" / script)]

    def blender(directory, script):
        return [
            "blender",
            "--background",
            "--threads",
            "4",
            "--python-exit-code",
            "1",
            "--python",
            str(SCRIPTS / directory / script),
        ]

    production = [
        ("render", python("render_sculpture_samples.py")),
        ("hand-closeups", blender("animation_samples", "render_hand_closeups.py")),
        ("shoulder-review", blender("animation_samples", "render_squat_review.py")),
        ("export-character", blender("character_assets", "export_hand_rig.py")),
        ("collision-gate", python("validate_collisions.py")),
        ("package", python("package_sculpture_samples.py")),
    ]
    verification = [
        ("verify-grips", blender("animation_samples", "verify_hand_grips.py")),
        ("verify-shoulders", blender("animation_samples", "verify_squat_shoulders.py")),
        (
            "verify-deformation",
            blender("animation_samples", "verify_sculpture_deformation.py"),
        ),
        ("verify-character", blender("character_assets", "verify_hand_assets.py")),
        ("verify-media", python("verify_sculpture_samples.py")),
    ]
    if mode == "verify":
        verification.insert(0, ("verify-collisions", python("validate_collisions.py")))
    return (production if mode == "full" else []) + verification


def preflight(mode):
    missing = [
        name for name in ("blender", "ffmpeg", "ffprobe") if not shutil.which(name)
    ]
    if importlib.util.find_spec("PIL") is None:
        missing.append("Pillow in the selected Python interpreter")
    required = []
    for sex in ("male", "female"):
        required.append(
            ROOT
            / f"docs/character-assets/muscle-overlay-v1/{sex}/greek-{sex}-muscles.blend"
        )
        if mode == "verify":
            required.append(
                ROOT
                / f"docs/character-assets/hand-rig-v1/{sex}/greek-{sex}-hand-rig.glb"
            )
            for exercise in EXERCISES:
                for ext in ("blend", "mp4", "gif"):
                    required.append(
                        ROOT / f"docs/animation-samples-v2/{sex}/{exercise}.{ext}"
                    )
                folder = ROOT / f"build/animation-samples-v2/{sex}/{exercise}"
                required.append(folder / "motion-checks.json")
                required.extend(
                    folder / f"frames/frame-{frame:04d}.png" for frame in range(1, 121)
                )
    if mode == "full":
        # Card typography currently targets the original macOS production host.
        required.extend(
            Path(p)
            for p in (
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
            )
        )
        required.extend(
            ROOT / f"docs/animation-samples-v2/shoulder-review/before-{view}.png"
            for view in ("front", "back")
        )
    absent = [str(p) for p in required if not p.exists()]
    if missing or absent:
        details = "\n".join(missing + absent[:12])
        if len(absent) > 12:
            details += f"\n... and {len(absent)-12} other missing files"
        raise RuntimeError(
            "Preflight failed:\n"
            + details
            + "\nOn a fresh checkout use --mode full to regenerate ignored render frames."
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["full", "verify"], default="full")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print ordered commands without writing files or running tools",
    )
    args = parser.parse_args()
    jobs = stages(args.mode)
    if args.dry_run:
        for name, command in jobs:
            print(f"{name}: {shlex.join(command)}")
        return 0
    preflight(args.mode)
    BUILD.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = BUILD / stamp
    run_dir.mkdir()
    receipt = {
        "mode": args.mode,
        "started_at": stamp,
        "status": "running",
        "stages": [],
    }
    receipt_path = run_dir / "run.json"

    def save():
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")

    save()
    for name, command in jobs:
        print(f'[{name}] running; log: {run_dir / (name + ".log")}', flush=True)
        row = {"name": name, "command": command, "status": "running"}
        receipt["stages"].append(row)
        save()
        try:
            with (run_dir / f"{name}.log").open("w") as log:
                subprocess.run(
                    command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True
                )
        except (subprocess.CalledProcessError, OSError, KeyboardInterrupt) as error:
            row["status"] = "failed"
            row["error"] = str(error)
            receipt["status"] = "failed"
            save()
            raise
        row["status"] = "passed"
        save()
    receipt["status"] = "passed"
    receipt["visual_review_required"] = True
    save()
    print(
        f"Pipeline passed: {receipt_path}\nVisual movement review is still required before publishing."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
