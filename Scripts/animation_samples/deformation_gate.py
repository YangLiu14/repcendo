"""Require both mechanical regression checks and scene-matched visual review."""
import hashlib
import json
import math
from pathlib import Path

try:
    from .collision_gate import CATALOG, ROOT
    from .plan_exercises import PLAN_EXERCISES
except ImportError:
    from collision_gate import CATALOG, ROOT
    from plan_exercises import PLAN_EXERCISES


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_pec_deck_pass(sex, exercise, root):
    if exercise not in ("pec_fly", "reverse_fly"):
        return
    folder = root / "docs/animation-plan-v3"
    path = folder / "pec-deck-validation.json"
    records = json.loads(path.read_text()) if path.exists() else {}
    report = records.get(sex + "/" + exercise, {})
    links = report.get("link_length_variation_m", {})
    valid = (
        report.get("passed") is True
        and report.get("sceneSHA256") == digest(folder / sex / (exercise + ".blend"))
        and report.get("validatorSHA256")
        == digest(Path(__file__).with_name("verify_pec_deck.py"))
        and report.get("referenceSHA256")
        == digest(ROOT / "docs/equipment-references/pec-deck.json")
        and report.get("frames") == list(range(1, 122))
        and 0 <= report.get("max_joint_error_m", 1) < 1e-4
        and 0 <= report.get("max_grip_axis_error", 1) < 1e-5
        and set(links) == {s + p for s in ("Left", "Right") for p in ("boom", "hanger")}
        and all(math.isfinite(v) and 0 <= v < 1e-5 for v in links.values())
    )
    if not valid:
        raise RuntimeError(
            f"{sex}/{exercise}: missing, stale or failed photo-referenced mechanism audit"
        )


def require_axilla_strain_pass(sex, exercise, root):
    if exercise != "dead_bug":
        return
    folder = root / "docs/animation-plan-v3" / sex
    path = folder / "dead_bug-strain.json"
    report = json.loads(path.read_text()) if path.exists() else {}
    samples = report.get("samples", [])
    valid = (
        report.get("status") == "strain_probe_passed_visual_review_still_required"
        and report.get("scene_sha256") == digest(folder / "dead_bug.blend")
        and report.get("validator_sha256")
        == digest(Path(__file__).with_name("diagnose_torso_strain.py"))
        and report.get("threshold_p95") == 1.8
        and report.get("edges_checked", 0) >= 100
        and [s.get("frame") for s in samples] == list(range(1, 194))
        and all(
            math.isfinite(s.get("p95", float("nan"))) and 0 < s["p95"] <= 1.8
            for s in samples
        )
    )
    if not valid:
        raise RuntimeError(
            f"{sex}/{exercise}: missing, stale or failed full-cycle axillary strain audit"
        )


def require_grip_orientation_pass(sex, exercise, root):
    """Motion-specific grip intent supplements surface/contact checks."""
    if exercise != "cable_crunch":
        return
    folder = root / "docs/animation-plan-v3"
    path = folder / "grip-orientation-validation.json"
    records = json.loads(path.read_text()) if path.exists() else {}
    r = records.get(sex + "/" + exercise, {})
    valid = (
        r.get("passed") is True
        and r.get("failures") == []
        and r.get("frames") == list(range(1, CATALOG[exercise].get("frames", 120) + 2))
        and r.get("sceneSHA256") == digest(folder / sex / (exercise + ".blend"))
        and r.get("validatorSHA256")
        == digest(Path(__file__).with_name("verify_grip_orientation.py"))
        and 0 <= r.get("max_wrist_twist_deg", 999) <= 90
        and 0 <= r.get("max_wrist_bend_deg", 999) <= 15
        and 0.25 <= r.get("min_thumb_up_dot", -1) <= 1
        and 0.5 <= r.get("min_palm_inward_dot", -1) <= 1
    )
    if not valid:
        raise RuntimeError(
            f"{sex}/{exercise}: missing, stale or failed grip orientation audit"
        )


def require_deformation_pass(sex=None, exercise=None, root=None):
    root = root or ROOT
    folder = root / "docs/animation-plan-v3"
    evidence = json.loads((folder / "deformation-validation.json").read_text())
    reviews = json.loads((folder / "deformation-visual-review.json").read_text())
    for s in [sex] if sex else ["male", "female"]:
        for name in [exercise] if exercise else CATALOG:
            if name == "squat":
                continue
            require_grip_orientation_pass(s, name, root)
            try:
                from .equipment_gate import require_equipment_pass
            except ImportError:
                from equipment_gate import require_equipment_pass
            require_equipment_pass(s, name, root)
            require_pec_deck_pass(s, name, root)
            require_axilla_strain_pass(s, name, root)
            key = s + "/" + name
            r = evidence.get(key, {})
            v = reviews.get(key, {})
            collection = (
                "animation-plan-v3"
                if name in PLAN_EXERCISES
                else "animation-samples-v2"
            )
            scene = root / f"docs/{collection}/{s}/{name}.blend"
            sha = digest(scene)
            good = (
                r.get("status") == "automated_checks_passed"
                and r.get("failures") == []
                and r.get("scene_sha256") == sha
                and r.get("validator_sha256")
                == digest(Path(__file__).with_name("deformation_audit.py"))
                and r.get("frames")
                == list(range(1, CATALOG[name].get("frames", 120) + 2))
                and v.get("status") == "accepted"
                and v.get("scene_sha256") == sha
                and set(v.get("views", [])) == {"front", "side", "back"}
                and len(v.get("frames", [])) >= 4
                and set(r.get("review_frames", [])).issubset(v.get("frames", []))
                and bool(v.get("notes"))
                and bool(v.get("evidence"))
            )
            if good:
                good = all(
                    (root / path).is_file() and digest(root / path) == expected
                    for path, expected in v["evidence"].items()
                )
            if good and name == "cable_crunch":
                good = (
                    f"docs/animation-plan-v3/deformation-review/{s}/cable_crunch-grips.jpg"
                    in v["evidence"]
                )
            if good and name == "dead_bug":
                good = (
                    f"docs/animation-plan-v3/deformation-review/{s}/dead_bug-shoulders.jpg"
                    in v["evidence"]
                )
            if good and name in ("pec_fly", "reverse_fly"):
                good = (
                    f"docs/animation-plan-v3/equipment-review/{s}/{name}.jpg"
                    in v["evidence"]
                )
            if not good:
                raise RuntimeError(
                    f"{key}: missing, stale or failed deformation checks / multi-view visual review"
                )
    return evidence
