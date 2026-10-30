"""Refuse equipment-refitted production without matching photographic evidence."""
import hashlib, json, math
from pathlib import Path
try:
    from .equipment_refit_catalog import MOTIONS, LIBRARY_MOTIONS
except ImportError:
    from equipment_refit_catalog import MOTIONS, LIBRARY_MOTIONS

ROOT = Path(__file__).resolve().parents[2]


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def require_equipment_pass(sex, name, root=ROOT, visual=True):
    if name not in MOTIONS:
        return
    col = (
        "animation-library"
        if name in LIBRARY_MOTIONS
        else ("animation-samples-v2" if name == "row" else "animation-plan-v3")
    )
    scene = root / f"docs/{col}/{sex}/{name}.blend"
    folder = root / "docs/animation-plan-v3"
    path = folder / "equipment-validation.json"
    records = json.loads(path.read_text()) if path.exists() else {}
    r = records.get(sex + "/" + name, {})
    try:
        from .collision_gate import CATALOG
        from .library_exercises import LIBRARY_EXERCISES
    except ImportError:
        from collision_gate import CATALOG
        from library_exercises import LIBRARY_EXERCISES

    config = LIBRARY_EXERCISES[name] if name in LIBRARY_MOTIONS else CATALOG[name]
    if not (
        r.get("passed") is True
        and r.get("failures") == []
        and r.get("frames") == list(range(1, config.get("frames", 120) + 2))
        and r.get("sceneSHA256") == digest(scene)
        and r.get("validatorSHA256")
        == digest(Path(__file__).with_name("verify_equipment_refit.py"))
        and r.get("referenceSHA256")
        == digest(ROOT / "docs/equipment-references/equipment-audit.json")
    ):
        raise RuntimeError(
            f"{sex}/{name}: missing, stale or failed equipment mechanism checks"
        )
    limits = {"fixed_drift": 1e-5, "link_length_variation": .001, "slide_error": .0001, "cable_error": 1e-5}
    metrics = r.get("metrics", {})
    if not all(isinstance(metrics.get(k), (int, float)) and math.isfinite(metrics[k]) and 0 <= metrics[k] <= limit for k, limit in limits.items()):
        raise RuntimeError(f"{sex}/{name}: invalid equipment measurements")
    if r.get("bodyProofSHA256"):
        proof = folder / "equipment-body-proof.json"
        if not proof.is_file() or digest(proof) != r["bodyProofSHA256"]:
            raise RuntimeError(f"{sex}/{name}: body reuse proof changed")
    if visual:
        path = folder / "equipment-visual-review.json"
        v = (
            json.loads(path.read_text()).get(sex + "/" + name, {})
            if path.exists()
            else {}
        )
        if not (
            v.get("status") == "accepted"
            and v.get("sceneSHA256") == digest(scene)
            and v.get("notes")
            and set(v.get("views", [])) == {"main", "side"}
            and v.get("evidence")
            and all(
                (root / p).is_file() and digest(root / p) == h
                for p, h in v["evidence"].items()
            )
        ):
            raise RuntimeError(
                f"{sex}/{name}: missing or stale equipment photo comparison"
            )
    return r
