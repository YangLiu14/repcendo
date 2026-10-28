"""Independent Blender inspection of final baked scenes and planted foot mesh."""
import bpy, json, sys
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/animation-samples-v2"
report = {}
for sex in ["male", "female"]:
    for name in ["squat", "bench", "row"]:
        bpy.ops.wm.open_mainfile(filepath=str(OUT / sex / f"{name}.blend"))
        scene = bpy.context.scene
        rig = next(o for o in scene.objects if o.type == "ARMATURE")
        obj = next(
            o
            for o in scene.objects
            if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)
        )
        feet = np.array(
            [v.index for v in obj.data.vertices if v.co.z < 0.025], dtype=int
        )
        first = None
        maximum = 0
        bounds = []
        for frame in [1, 31, 61, 91, 121]:
            scene.frame_set(frame)
            graph = bpy.context.evaluated_depsgraph_get()
            evaluated = obj.evaluated_get(graph)
            mesh = evaluated.to_mesh()
            try:
                coords = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
                mesh.vertices.foreach_get("co", coords)
                coords = coords.reshape(-1, 3)
                assert np.isfinite(coords).all()
                mat = np.array(evaluated.matrix_world)
                points = coords @ mat[:3, :3].T + mat[:3, 3]
                assert np.abs(points).max() < 5
                if first is None:
                    first = points[feet].copy()
                maximum = max(
                    maximum, float(np.linalg.norm(points[feet] - first, axis=1).max())
                )
                bounds.append(
                    {
                        "frame": frame,
                        "min": points.min(axis=0).tolist(),
                        "max": points.max(axis=0).tolist(),
                    }
                )
            finally:
                evaluated.to_mesh_clear()
        assert maximum < 1e-4, (sex, name, maximum)
        report[sex + "/" + name] = {
            "frames_checked": [1, 31, 61, 91, 121],
            "finite_vertices": True,
            "foot_surface_vertices": len(feet),
            "max_foot_surface_drift_m": maximum,
            "character_bounds": bounds,
        }
(OUT / "deformation-validation.json").write_text(
    json.dumps({"status": "passed", "samples": report}, indent=2) + "\n"
)
print(
    "DEFORMATION_PASS",
    len(report),
    "scenes; finite mesh and planted foot-surface drift < 0.1 mm",
)
