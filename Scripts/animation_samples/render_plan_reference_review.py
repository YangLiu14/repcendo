"""Produce scene-bound main/front/side/back reference evidence; never approve."""
import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).parent))
from plan_reference_gate import CATALOG, ROOT, digest, folder
from frame_plan_scene import fit

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--root', type=Path, default=ROOT)
p.add_argument('--exercise', choices=list(CATALOG), required=True)
p.add_argument('--sex', choices=['male', 'female'], required=True)
a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
source = folder(a.root, a.sex, a.exercise) / f'{a.exercise}.blend'
sha = digest(source)
bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
s = bpy.context.scene
out = a.root / f'build/plan-reference-review/{a.sex}/{a.exercise}'
out.mkdir(parents=True, exist_ok=True)
s.render.resolution_x = s.render.resolution_y = 600
s.render.resolution_percentage = 100
s.eevee.taa_render_samples = 16
frames = [1, 31, 61, 91] if s.frame_end == 120 else [1, 25, 49, 73, 97, 121, 145, 169]
original = s.camera.matrix_world.copy()
for view, offset in [('main', None), ('front', (0,5,.4)), ('side', (5,0,.4)), ('back', (0,-5,.4))]:
    if offset is None:
        s.camera.matrix_world = original
    else:
        center = Vector((0,.1,.9))
        if a.exercise in ('dead_bug', 'reverse_crunch') and view in ('front', 'back'):
            offset = (0, 0, 5 if view == 'front' else -5)
        s.camera.location = center + Vector(offset)
        s.camera.rotation_euler = (center-s.camera.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()
    fit(s)
    for f in frames:
        s.frame_set(f)
        s.render.filepath = str((out/f'{view}-{f:04d}.png').resolve())
        bpy.ops.render.render(write_still=True)
assert digest(source) == sha
(out/'source.json').write_text(json.dumps(dict(sceneSHA256=sha, frames=frames,
    views=['main','front','side','back']), indent=2)+'\n')
