"""Fail closed on missing, partial, failed, or stale collision evidence."""
import hashlib
import json
from pathlib import Path

try:
    from .plan_exercises import PLAN_EXERCISES
    from .exercise_catalog import EXERCISES
except ImportError:
    from plan_exercises import PLAN_EXERCISES
    from exercise_catalog import EXERCISES

ROOT = Path(__file__).resolve().parents[2]
CATALOG = {k: v for k, v in {**EXERCISES, **PLAN_EXERCISES}.items() if k != "squat"}
REPORT = ROOT / "docs/animation-plan-v3/collision-validation.json"


def validator_digest():
    return hashlib.sha256(
        (Path(__file__).parent / "collision_audit.py").read_bytes()
    ).hexdigest()


def require_collision_pass(sex=None, exercise=None, report=None, root=None):
    root = root or ROOT
    report = report or root / "docs/animation-plan-v3/collision-validation.json"
    evidence = json.loads(report.read_text())
    for s in [sex] if sex else ["male", "female"]:
        for name in [exercise] if exercise else CATALOG:
            if name == "squat":
                continue  # This report covers the 19 motions in the supplied plan.
            key = s + "/" + name
            r = evidence.get(key, {})
            collection = (
                "animation-plan-v3"
                if name in PLAN_EXERCISES
                else "animation-samples-v2"
            )
            scene = root / f"docs/{collection}/{s}/{name}.blend"
            expected_frames = list(range(1, CATALOG[name].get("frames", 120) + 2))
            valid = (
                r.get("passed") is True
                and r.get("hits") == []
                and r.get("auditVersion") == 2
                and r.get("validatorSHA256") == validator_digest()
                and r.get("frames") == expected_frames
                and r.get("tolerance_m") == 0.002
                and r.get("checks")
                == dict(
                    body_in_equipment=True,
                    equipment_in_body=True,
                    nonlocal_self_intersection=True,
                )
                and r.get("sceneSHA256")
                == hashlib.sha256(scene.read_bytes()).hexdigest()
            )
            if not valid:
                raise RuntimeError(
                    f"{key}: missing, failed, partial or stale collision validation. Run validate_collisions.py before rendering/export."
                )
    return evidence


def record_media(sex, name):
    if name == "squat":
        return
    try:
        from .deformation_gate import require_deformation_pass
    except ImportError:
        from deformation_gate import require_deformation_pass

    require_deformation_pass(sex, name)
    r = require_collision_pass(sex, name)[sex + "/" + name]
    collection = (
        "animation-plan-v3" if name in PLAN_EXERCISES else "animation-samples-v2"
    )
    folder = ROOT / f"docs/{collection}/{sex}"
    stamp = dict(
        sceneSHA256=r["sceneSHA256"], validatorSHA256=validator_digest(), files={}
    )
    for suffix in [".mp4", "-poster.png"]:
        file = folder / f"{name}{suffix}"
        stamp["files"][file.name] = hashlib.sha256(file.read_bytes()).hexdigest()
    (folder / f"{name}-media.json").write_text(json.dumps(stamp, indent=2) + "\n")


def require_render_pass(sex, name):
    if name == "squat":
        return
    try:
        from .deformation_gate import require_deformation_pass
    except ImportError:
        from deformation_gate import require_deformation_pass

    require_deformation_pass(sex, name)
    r = require_collision_pass(sex, name)[sex + "/" + name]
    collection = (
        "animation-plan-v3" if name in PLAN_EXERCISES else "animation-samples-v2"
    )
    folder = ROOT / f"build/{collection}/{sex}/{name}"
    assert (
        json.loads((folder / "render-source.json").read_text())["sha256"]
        == r["sceneSHA256"]
    ), "Render scene hash differs from audited scene"
    assert all(
        (folder / f"frames/frame-{f:04d}.png").exists()
        for f in range(1, CATALOG[name].get("frames", 120) + 1)
    ), "Incomplete rendered cycle"


def require_media_pass():
    try:
        from .deformation_gate import require_deformation_pass
    except ImportError:
        from deformation_gate import require_deformation_pass

    require_deformation_pass()
    evidence = require_collision_pass()
    for key, r in evidence.items():
        sex, name = key.split("/")
        collection = (
            "animation-plan-v3" if name in PLAN_EXERCISES else "animation-samples-v2"
        )
        folder = ROOT / f"docs/{collection}/{sex}"
        stamp = json.loads((folder / f"{name}-media.json").read_text())
        assert stamp["sceneSHA256"] == r["sceneSHA256"], f"Stale packaged media: {key}"
        assert (
            stamp["validatorSHA256"] == validator_digest()
        ), f"Stale media validation: {key}"
        assert set(stamp["files"]) == {
            name + ".mp4",
            name + "-poster.png",
        }, f"Incomplete media receipt: {key}"
        for filename, digest in stamp["files"].items():
            assert (
                hashlib.sha256((folder / filename).read_bytes()).hexdigest() == digest
            ), f"Modified media: {key}/{filename}"
