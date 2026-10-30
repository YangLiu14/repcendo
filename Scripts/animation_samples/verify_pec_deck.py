"""Check the photographed mechanism: fixed pivots, rigid links and grip joins."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]


def verify(path):
    bpy.ops.wm.open_mainfile(filepath=str(path.resolve()))
    s = bpy.context.scene
    reference = ROOT / "docs/equipment-references/pec-deck.json"
    assert (
        s.get("equipment_reference_sha256")
        == hashlib.sha256(reference.read_bytes()).hexdigest()
    ), "Missing/stale photo reference"
    assert s.get("equipment_mechanism_version") == "pec-deck-fixed-pivots-1"
    assert all(
        s.objects.get(n)
        for n in ["Pec stack guard", "Pec pad brace", "Pec pad upright", "Seat cushion"]
    )
    lengths = {}
    pivots = {}
    max_joint = 0.0
    max_grip_axis = 0.0
    for f in range(1, s.frame_end + 2):
        s.frame_set(f)
        for side in ["Left", "Right"]:
            boom = s.objects["Pec rotating boom " + side]
            hanger = s.objects["Pec descending arm " + side]
            grip = s.objects["Grip." + side]
            pivot = s.objects["Pec pivot " + side].location
            endpoints = lambda o: [
                o.matrix_world @ Vector((0, 0, z)) for z in [-0.5, 0.5]
            ]
            a, b = endpoints(boom)
            c, d = endpoints(hanger)
            key = side
            pivots.setdefault(key, tuple(a))
            assert (a - Vector(pivots[key])).length < 1e-5
            # Pivot cylinder center is 1 cm above the boom's axis.
            max_joint = max(
                max_joint,
                (a - (pivot - Vector((0, 0, 0.01)))).length,
                (b - c).length,
                (d - (grip.location + grip.matrix_world.to_3x3().col[0] * 0.09)).length,
            )
            max_grip_axis = max(
                max_grip_axis, 1 - abs(grip.matrix_world.to_3x3().col[0].normalized().z)
            )
            for name, obj in [("boom", boom), ("hanger", hanger)]:
                lengths.setdefault(side + name, []).append(obj.scale.z)
    spans = {k: max(v) - min(v) for k, v in lengths.items()}
    assert max(spans.values()) < 1e-5, spans
    assert max_joint < 1e-4, max_joint
    assert max_grip_axis < 1e-5, max_grip_axis
    return dict(
        passed=True,
        sceneSHA256=hashlib.sha256(path.read_bytes()).hexdigest(),
        validatorSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        referenceSHA256=hashlib.sha256(reference.read_bytes()).hexdigest(),
        frames=list(range(1, s.frame_end + 2)),
        max_joint_error_m=max_joint,
        max_grip_axis_error=max_grip_axis,
        link_length_variation_m=spans,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    a = p.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    result = {}
    for sex in ["male", "female"]:
        for exercise in ["pec_fly", "reverse_fly"]:
            result[sex + "/" + exercise] = verify(
                a.root / f"docs/animation-plan-v3/{sex}/{exercise}.blend"
            )
    out = a.root / "docs/animation-plan-v3/pec-deck-validation.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print("PEC_DECK_PASS", len(result))
