"""Full-loop fixed-frame, rigid-link, slide and cable conservation checks.
Also proves that equipment-only refits leave the evaluated athlete unchanged.
"""
import argparse, json, hashlib, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).parent))
from equipment_refit_catalog import MOTIONS, LIBRARY_MOTIONS
from collision_audit import mesh_data

ROOT = Path(__file__).resolve().parents[2]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def body_hash(s):
    body = next(
        o
        for o in s.objects
        if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)
    )
    h = hashlib.sha256()
    for f in range(1, s.frame_end + 2):
        s.frame_set(f)
        coords, tris = mesh_data(body, bpy.context.evaluated_depsgraph_get())
        h.update(coords.tobytes())
        h.update(np.asarray(tris, dtype=np.int32).tobytes())
    return h.hexdigest()


def inspect(s):
    failures = []
    metric = {
        "fixed_drift": 0.0,
        "link_length_variation": 0.0,
        "slide_error": 0.0,
        "cable_error": 0.0,
    }
    if s.get("equipment_refit_version") != "photo-equipment-1":
        return ["Missing photo refit"], metric
    if s.get("equipment_reference_sha256") != sha(ROOT / "docs/equipment-references/equipment-audit.json"):
        failures.append("Scene photograph reference is stale")
    c = json.loads(s["equipment_constraints"])
    s.frame_set(1)
    mats = {n: np.array(s.objects[n].matrix_world) for n in c["fixed"]}
    lengths = {n: [] for n in c["rigid"]}
    cable_values = {r["cable"]: [] for r in c["rules"] if r["kind"] == "cable_stack"}
    for f in range(1, s.frame_end + 2):
        s.frame_set(f)
        bpy.context.view_layer.update()
        for n, m in mats.items():
            metric["fixed_drift"] = max(
                metric["fixed_drift"],
                float(np.max(abs(np.array(s.objects[n].matrix_world) - m))),
            )
        for n in lengths:
            lengths[n].append(s.objects[n].matrix_world.to_3x3().col[2].length)
        for r in c["rules"]:
            if r["kind"] == "slide":
                delta = s.objects[r["object"]].matrix_world.translation - Vector(
                    r["origin"]
                )
                axis = Vector(r["axis"])
                err = (delta - axis * delta.dot(axis)).length
                metric["slide_error"] = max(metric["slide_error"], err)
            if r["kind"] == "cable_stack":
                length = s.objects[r["cable"]].matrix_world.to_3x3().col[2].length
                z = s.objects[r["plates"][0]].location.z
                cable_values[r["cable"]].append(length - z)
    for v in lengths.values():
        metric["link_length_variation"] = max(
            metric["link_length_variation"], max(v) - min(v)
        )
    for v in cable_values.values():
        metric["cable_error"] = max(metric["cable_error"], max(v) - min(v))
    for k, t in [
        ("fixed_drift", 1e-5),
        ("link_length_variation", 0.001),
        ("slide_error", 0.0001),
        ("cable_error", 1e-5),
    ]:
        if metric[k] > t:
            failures.append(f"{k}: {metric[k]} > {t}")
    return failures, metric


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--before", type=Path)
    p.add_argument("--exercise", choices=MOTIONS)
    a = p.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    records = {}
    for sex in ["male", "female"]:
        for n in [a.exercise] if a.exercise else MOTIONS:
            col = (
                "animation-library"
                if n in LIBRARY_MOTIONS
                else ("animation-samples-v2" if n == "row" else "animation-plan-v3")
            )
            rel = Path(f"docs/{col}/{sex}/{n}.blend")
            path = a.root / rel
            bpy.ops.wm.open_mainfile(filepath=str(path.resolve()))
            s = bpy.context.scene
            frames = list(range(1, s.frame_end + 2))
            failures, metrics = inspect(s)
            bh = body_hash(s) if a.before else None
            if a.before:
                bpy.ops.wm.open_mainfile(filepath=str((a.before / rel).resolve()))
                old = body_hash(bpy.context.scene)
                if bh != old:
                    failures.append("Athlete surface changed")
            records[sex + "/" + n] = dict(
                passed=not failures,
                failures=failures,
                metrics=metrics,
                frames=frames,
                sceneSHA256=sha(path),
                validatorSHA256=sha(Path(__file__)),
                referenceSHA256=sha(
                    ROOT / "docs/equipment-references/equipment-audit.json"
                ),
                bodySHA256=bh,
                originalSceneSHA256=sha(a.before / rel) if a.before else None,
            )
            print(sex, n, failures or "PASS", flush=True)
    out = a.root / "docs/animation-plan-v3/equipment-validation.json"
    previous = json.loads(out.read_text()) if out.exists() and a.exercise else {}
    previous.update(records)
    out.write_text(json.dumps(previous, indent=2) + "\n")
    if any(not r["passed"] for r in records.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
