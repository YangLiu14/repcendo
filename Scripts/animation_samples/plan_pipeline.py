"""19-plan-motion production: bake → collide → render → validate → package → App.

Use --from-scenes to validate and export already edited scenes without rebaking.
Requires Blender, ffmpeg, and Python with Pillow. No training records are touched.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--from-scenes", action="store_true")
p.add_argument("--workers", type=int, default=2)
p.add_argument("--dry-run", action="store_true")
p.add_argument(
    "--prepare-review",
    action="store_true",
    help="Bake/check and produce pending visual evidence, without exporting media",
)
a = p.parse_args()


def py(name, *args):
    return [sys.executable, str(HERE / name), *args]


def blender(name):
    return [
        "/opt/homebrew/bin/blender",
        "-b",
        "-t",
        "2",
        "--python-exit-code",
        "1",
        "--python",
        str(HERE / name),
    ]


from plan_reference_gate import CATALOG as REFERENCE_CATALOG, load_reference

if not a.dry_run:
    for name in REFERENCE_CATALOG:
        load_reference(name)

steps = []
if not a.from_scenes:
    steps.append(py("render_plan.py", "--bake-only", "--workers", str(a.workers)))
steps += [
    blender("../character_assets/test_character_binding.py"),
    blender("test_collision_audit.py"),
    py("test_collision_gate.py"),
    py("test_deformation_gate.py"),
    py("test_pec_deck_gate.py"),
    py("test_equipment_gate.py"),
    py("validate_collisions.py", "--workers", str(a.workers)),
    py("validate_deformations.py", "--workers", str(a.workers)),
    blender("verify_grip_orientation.py"),
    blender("verify_pec_deck.py"),
    [*blender("verify_equipment_refit.py"), "--"],
]
for name in REFERENCE_CATALOG:
    for sex in ("male", "female"):
        steps.append([*blender("plan_reference_gate.py"), "--", "--exercise", name, "--sex", sex])
if a.prepare_review:
    for name in REFERENCE_CATALOG:
        for sex in ("male", "female"):
            steps.append([*blender("render_plan_reference_review.py"), "--", "--exercise", name, "--sex", sex])
    steps.append(py("compose_plan_reference_review.py"))
    steps += [
        [*blender("render_deformation_review.py"), "--"],
        py("compose_deformation_review.py"),
        blender("render_pec_deck_review.py"),
        py("compose_pec_deck_review.py"),
        blender("render_equipment_review.py"),
        py("compose_equipment_review.py"),
    ]
else:
    steps += [
        py(
            "render_plan.py",
            "--workers",
            str(a.workers),
            "--references",
        ),
        blender("verify_plan_grips.py"),
        blender("verify_plan_scenes.py"),
        py("package_plan.py"),
        py("package_sculpture_samples.py", "--exercise", "bench"),
        py("package_sculpture_samples.py", "--exercise", "row"),
        py("package_plan.py", "--page-only"),
        [sys.executable, str(ROOT / "Scripts/prepare_animations.py")],
        py("verify_plan_assets.py", "--bundle"),
    ]
for command in steps:
    print(" ".join(command), flush=True)
    if not a.dry_run:
        subprocess.run(command, cwd=ROOT, check=True)
if a.prepare_review:
    print(
        "Review reference-review and deformation-review images against the human sources; record scene-matched reference-review.json and deformation-visual-review.json decisions; then use --from-scenes."
    )
