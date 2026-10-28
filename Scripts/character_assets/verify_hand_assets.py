"""Re-import portable GLBs and verify weighted fingers and open/close motion."""
import bpy, json, struct
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/character-assets/hand-rig-v1"
report = {}
for sex in ["male", "female"]:
    p = OUT / sex / f"greek-{sex}-hand-rig.glb"
    raw = p.read_bytes()
    length = struct.unpack_from("<I", raw, 12)[0]
    doc = json.loads(raw[20 : 20 + length])
    assert len(doc["skins"][0]["joints"]) == 53
    assert len(doc["animations"]) == 1
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(p))
    rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
    mesh = next(o for o in bpy.context.scene.objects if o.type == "MESH")
    fingers = [
        b.name
        for b in rig.data.bones
        if any(
            "Hand" + d in b.name for d in ["Thumb", "Index", "Middle", "Ring", "Pinky"]
        )
    ]
    assert len(fingers) == 30
    used = {n: 0 for n in fingers}
    sums = []
    for v in mesh.data.vertices:
        sums.append(sum(g.weight for g in v.groups))
        for g in v.groups:
            n = mesh.vertex_groups[g.group].name
            if n in used and g.weight > 0.05:
                used[n] += 1
    assert min(used.values()) > 0 and min(sums) > 0.999 and max(sums) < 1.001
    scene = bpy.context.scene
    # glTF may change FPS; use the imported action frame range.
    action = rig.animation_data.action
    start, end = action.frame_range
    middle = (start + end) / 2
    clouds = []
    for frame in [start, middle, end]:
        scene.frame_set(round(frame))
        ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
        me = ev.to_mesh()
        points = np.array([list(v.co) for v in me.vertices])
        ev.to_mesh_clear()
        assert np.isfinite(points).all()
        clouds.append(points)
    movement = np.linalg.norm(clouds[1] - clouds[0], axis=1)
    loop = np.linalg.norm(clouds[2] - clouds[0], axis=1)
    assert (movement > 0.001).sum() > 200 and loop.max() < 1e-4
    report[sex] = {
        "skin_joints": 53,
        "finger_bones": 30,
        "animation_count": 1,
        "weighted_vertices_per_finger_bone": used,
        "weight_sum_range": [min(sums), max(sums)],
        "moved_vertices": int((movement > 0.001).sum()),
        "max_open_close_displacement_model_units": float(movement.max()),
        "loop_error_model_units": float(loop.max()),
    }
(OUT / "validation.json").write_text(
    json.dumps(
        {"status": "passed", "glb_reimport": True, "characters": report}, indent=2
    )
    + "\n"
)
print(
    "HAND_ASSETS_PASS: GLB reimport, 53 joints, 30 weighted finger bones, one working open/close animation per character"
)
