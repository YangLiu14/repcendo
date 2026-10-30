"""Render a baked plan scene, with resumable frames or key-pose review mode."""
import argparse, sys
from pathlib import Path
import bpy

p = argparse.ArgumentParser()
p.add_argument("--output", type=Path, required=True)
p.add_argument("--review", action="store_true")
p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
a = p.parse_args(sys.argv[sys.argv.index("--") + 1 :])
s = bpy.context.scene
sys.path.insert(0, str(Path(__file__).resolve().parent))
if not a.review:
    from collision_gate import require_collision_pass
    from deformation_gate import require_deformation_pass

    require_collision_pass(s["sex"], s["exercise"], root=a.root)
    require_deformation_pass(s["sex"], s["exercise"], root=a.root)
folder = a.output / ("review" if a.review else "frames")
folder.mkdir(parents=True, exist_ok=True)
frames = (
    [1, 1 + s.frame_end // 4, 1 + s.frame_end // 2, 1 + 3 * s.frame_end // 4]
    if a.review
    else range(1, s.frame_end + 1)
)
for f in frames:
    target = folder / f"frame-{f:04d}.png"
    if target.exists():
        continue
    s.frame_set(f)
    s.render.filepath = str(target)
    bpy.ops.render.render(write_still=True)
