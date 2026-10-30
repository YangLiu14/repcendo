"""Per-motion publication gates for independently reviewed library batches."""
import hashlib
import json
from pathlib import Path
from library_exercises import LIBRARY_EXERCISES

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def specification_digest(name):
    return hashlib.sha256(json.dumps(LIBRARY_EXERCISES[name], sort_keys=True).encode()).hexdigest()


def validator_hashes(name=None):
    version = LIBRARY_EXERCISES[name].get("audit_version", 1) if name else 1
    if version not in (1, 3, 4, 5):
        raise ValueError(f"Unsupported library audit version: {version}")
    suffix = f"_v{version}" if version >= 3 else ""
    result = {file: digest(HERE / file) for file in (
        "collision_audit.py", "deformation_audit.py", f"library_audit{suffix}.py", f"library_scene{suffix}.py",
    )}
    if version == 5:
        result["equipment-reference"] = digest(ROOT / "docs/equipment-references/batch-005.json")
    return result


def paths(root, sex, name):
    if sex not in ("male", "female") or name not in LIBRARY_EXERCISES:
        raise ValueError(f"Unknown library variant: {sex}/{name}")
    return root / "docs/animation-library" / sex, root / "build/animation-library" / sex / name


def require_scene_pass(sex, name, root=ROOT, visual=True):
    from equipment_gate import require_equipment_pass
    require_equipment_pass(sex, name, root, visual=visual)
    folder, _ = paths(root, sex, name)
    scene = folder / f"{name}.blend"
    audit = json.loads((folder / f"{name}-audit.json").read_text())
    frames = list(range(1, LIBRARY_EXERCISES[name].get("frames", 120) + 2))
    if not (
        audit.get("status") == "passed"
        and audit.get("sceneSHA256") == digest(scene)
        and audit.get("validatorSHA256") == validator_hashes(name)
        and (LIBRARY_EXERCISES[name].get("audit_version", 1) < 3 or audit.get("specificationSHA256") == specification_digest(name))
        and audit.get("frames") == frames
        and audit.get("collision", {}).get("hits") == []
        and audit.get("collision", {}).get("tolerance_m") == 0.002
        and audit["collision"].get("checks") == dict(body_in_equipment=True, equipment_in_body=True, nonlocal_self_intersection=True)
        and audit.get("deformation", {}).get("failures") == []
        and audit.get("motion", {}).get("failures") == []
    ):
        raise RuntimeError(f"{sex}/{name}: missing, failed, partial or stale library checks")
    if visual:
        review = json.loads((folder / f"{name}-review.json").read_text())
        if not (
            review.get("status") == "accepted"
            and review.get("sceneSHA256") == digest(scene)
            and set(review.get("views", [])) == {"main", "front", "side", "back", "grip"}
            and set(audit["deformation"]["review_frames"]).issubset(review.get("frames", []))
            and len(review.get("frames", [])) >= 4
            and review.get("notes")
            and review.get("evidence")
            and all((root / p).is_file() and digest(root / p) == sha for p, sha in review["evidence"].items())
        ):
            raise RuntimeError(f"{sex}/{name}: pending, rejected or stale visual review")
    return audit


def require_media_pass(sex, name, root=ROOT):
    require_scene_pass(sex, name, root)
    folder, _ = paths(root, sex, name)
    receipt = json.loads((folder / f"{name}-media.json").read_text())
    expected = {f"{name}.mp4", f"{name}-poster.png"}
    if not (
        receipt.get("sceneSHA256") == digest(folder / f"{name}.blend")
        and receipt.get("validatorSHA256") == validator_hashes(name)
        and (LIBRARY_EXERCISES[name].get("audit_version", 1) < 3 or receipt.get("specificationSHA256") == specification_digest(name))
        and set(receipt.get("files", {})) == expected
        and all(digest(folder / f) == sha for f, sha in receipt["files"].items())
        and receipt.get("mediaValidation", {}).get("decoded") is True
        and receipt["mediaValidation"].get("frames") == LIBRARY_EXERCISES[name].get("frames", 120)
        and receipt["mediaValidation"].get("clippedFrames") == []
    ):
        raise RuntimeError(f"{sex}/{name}: missing, stale or invalid packaged media")
    return receipt
