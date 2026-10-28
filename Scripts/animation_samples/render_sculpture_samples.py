"""Render v2 male/female exercise samples using two bounded local workers."""
import argparse, subprocess
from pathlib import Path
from exercise_catalog import EXERCISES
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[2]
P = argparse.ArgumentParser()
P.add_argument("--previews-only", action="store_true")
P.add_argument("--sex", choices=["male", "female", "both"], default="both")
P.add_argument("--exercise", choices=[*EXERCISES, "all"], default="all")
a = P.parse_args()
(ROOT / "build/animation-samples-v2").mkdir(exist_ok=True, parents=True)


def render(job):
    sex, exercise = job
    for view in ["motion", "front", "back"]:
        cmd = [
            "blender",
            "--background",
            "--threads",
            "5",
            "--python-exit-code",
            "1",
            "--python",
            str(ROOT / "Scripts/animation_samples/build_sculpture_scene.py"),
            "--",
            "--sex",
            sex,
            "--exercise",
            exercise,
            "--view",
            view,
        ]
        if a.previews_only:
            cmd.append("--preview")
        log = ROOT / f"build/animation-samples-v2/{sex}-{exercise}-{view}.log"
        with log.open("w") as f:
            subprocess.run(
                cmd, stdout=f, stderr=subprocess.STDOUT, check=True, cwd=ROOT
            )
        print(f"{sex}/{exercise}/{view} done", flush=True)


sexes = ["male", "female"] if a.sex == "both" else [a.sex]
with ThreadPoolExecutor(max_workers=2) as pool:
    list(
        pool.map(
            render,
            [
                (s, e)
                for s in sexes
                for e in (list(EXERCISES) if a.exercise == "all" else [a.exercise])
            ],
        )
    )
