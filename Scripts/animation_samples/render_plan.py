"""Bake and render the plan's original motions. Resume only from matching scene hashes."""
import argparse, concurrent.futures, hashlib, json, subprocess
from pathlib import Path
from plan_exercises import PLAN_EXERCISES
from collision_gate import require_collision_pass, CATALOG
from deformation_gate import require_deformation_pass

ROOT = Path(__file__).resolve().parents[2]
P = argparse.ArgumentParser()
P.add_argument("--review", action="store_true")
P.add_argument("--bake", action="store_true")
P.add_argument("--bake-only", action="store_true")
P.add_argument("--references", action="store_true")
P.add_argument("--sex", choices=["male", "female"])
P.add_argument("--exercise", choices=list(CATALOG))
P.add_argument("--exercises", nargs="+", choices=list(CATALOG))
P.add_argument("--workers", type=int, default=2)
P.add_argument("--output-root", type=Path, default=ROOT)
args = P.parse_args()


def command(cmd, log):
    with log.open("w") as out:
        proc = subprocess.run(cmd, stdout=out, stderr=subprocess.STDOUT, cwd=ROOT)
    text = log.read_text()
    if proc.returncode or "Traceback" in text:
        raise RuntimeError(f"{log}: {text[-1800:]}")


def render(pair):
    sex, name = pair
    collection = (
        "animation-plan-v3" if name in PLAN_EXERCISES else "animation-samples-v2"
    )
    folder = args.output_root / f"build/{collection}/{sex}/{name}"
    folder.mkdir(parents=True, exist_ok=True)
    scene = args.output_root / f"docs/{collection}/{sex}/{name}.blend"
    if args.bake or args.bake_only or not scene.exists():
        command(
            [
                "/opt/homebrew/bin/blender",
                "-b",
                "-t",
                "4",
                "--python",
                str(ROOT / "Scripts/animation_samples/build_sculpture_scene.py"),
                "--",
                "--sex",
                sex,
                "--exercise",
                name,
                "--no-render",
                "--output-root",
                str(args.output_root.resolve()),
            ],
            folder / "bake.log",
        )
        if name == "dead_bug":
            command(
                [
                    "/opt/homebrew/bin/blender",
                    "-b",
                    "-t",
                    "2",
                    "--python-exit-code",
                    "1",
                    "--python",
                    str(
                        ROOT / "Scripts/animation_samples/bake_shoulder_correctives.py"
                    ),
                    "--",
                    "--scene",
                    str(scene.resolve()),
                    "--output",
                    str(scene.resolve()),
                ],
                folder / "shoulder-corrective.log",
            )
            command(
                [
                    "/opt/homebrew/bin/blender",
                    "-b",
                    "-t",
                    "2",
                    "--python-exit-code",
                    "1",
                    "--python",
                    str(ROOT / "Scripts/animation_samples/diagnose_torso_strain.py"),
                    "--",
                    "--scene",
                    str(scene.resolve()),
                    "--all-frames",
                    "--output",
                    str(scene.with_name("dead_bug-strain.json").resolve()),
                ],
                folder / "shoulder-strain.log",
            )
    if args.bake_only:
        return sex, name
    if not args.review:
        require_collision_pass(sex, name, root=args.output_root)
        require_deformation_pass(sex, name, root=args.output_root)
    digest = hashlib.sha256(scene.read_bytes()).hexdigest()
    stamp = folder / "render-source.json"
    previous = json.loads(stamp.read_text()) if stamp.exists() else {}
    if previous.get("sha256") != digest:
        for directory in ["frames", "review"]:
            for f in (folder / directory).glob("frame-*.png"):
                f.unlink()
        stamp.write_text(json.dumps(dict(sha256=digest)))
    command(
        [
            "/opt/homebrew/bin/blender",
            "-b",
            str(scene),
            "-t",
            "4",
            "--python",
            str(ROOT / "Scripts/animation_samples/render_plan_scene.py"),
            "--",
            "--output",
            str(folder),
            "--root",
            str(args.output_root.resolve()),
        ]
        + (["--review"] if args.review else []),
        folder / ("review.log" if args.review else "render.log"),
    )
    if args.references:
        for view in ["front", "back"]:
            command(
                [
                    "/opt/homebrew/bin/blender",
                    "-b",
                    "-t",
                    "4",
                    "--python",
                    str(ROOT / "Scripts/animation_samples/build_sculpture_scene.py"),
                    "--",
                    "--sex",
                    sex,
                    "--exercise",
                    name,
                    "--view",
                    view,
                    "--output-root",
                    str(args.output_root.resolve()),
                ],
                folder / f"{view}.log",
            )
    print(f"DONE {sex}/{name}", flush=True)
    return sex, name


if __name__ == "__main__":
    pairs = [
        (s, n)
        for s in ([args.sex] if args.sex else ["male", "female"])
        for n in ([args.exercise] if args.exercise else args.exercises or CATALOG)
    ]
    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(render, pairs))
