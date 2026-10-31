"""Inventory the complete text library against original animation evidence.

This is a production worklist, not an animation generator or an approval tool.
Only exact dataset IDs associate a motion with an existing implementation.
It never changes animation metadata, review decisions, media or training plans.
"""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from collision_gate import require_collision_pass
from deformation_gate import require_deformation_pass
from exercise_catalog import EXERCISES
from plan_exercises import PLAN_EXERCISES
from library_exercises import LIBRARY_EXERCISES

ROOT = Path(__file__).resolve().parents[2]
SEXES = ("male", "female")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def inspect_variant(root, motion, sex, bundled):
    if motion in LIBRARY_EXERCISES:
        from library_gate import paths, require_scene_pass, require_media_pass
        folder, _ = paths(root, sex, motion)
        scene = folder / f"{motion}.blend"
        result = dict(scene=str(scene.relative_to(root)), sceneSHA256=sha256(scene) if scene.is_file() else None,
                      checks={}, issues=[], bundledBytes=0)
        from motion_reference_gate import require_reference_pass
        try:
            result['motionReferenceStatus'] = require_reference_pass(sex, motion, root)
        except (RuntimeError, OSError, ValueError, KeyError):
            result['motionReferenceStatus'] = 'blocked'
        for label, check in [("production", require_scene_pass), ("media", require_media_pass)]:
            try:
                check(sex, motion, root)
            except (RuntimeError, OSError, ValueError, KeyError) as error:
                result["checks"][label] = "blocked"
                result["issues"].append(str(error))
            else:
                result["checks"][label] = "passed"
        for field, suffix in [("video", ".mp4"), ("poster", "-poster.png")]:
            source = folder / f"{motion}{suffix}"
            name = bundled.get(field)
            target = root / "Repcendo/Resources/ExerciseAnimations" / name if isinstance(name, str) and Path(name).name == name else None
            if source.is_file() and target is not None and target.is_file() and sha256(source) == sha256(target) == bundled.get(field+"SHA256"):
                result["bundledBytes"] += target.stat().st_size
            else:
                result["issues"].append("Missing or changed bundled " + field)
        result["status"] = "blocked" if result["issues"] else "current_checks_passed"
        return result
    collection = (
        "animation-samples-v2" if motion in EXERCISES else "animation-plan-v3"
    )
    folder = root / "docs" / collection / sex
    scene = folder / f"{motion}.blend"
    result = {
        "scene": str(scene.relative_to(root)),
        "sceneSHA256": sha256(scene) if scene.is_file() else None,
        "checks": {},
        "issues": [],
    }
    if not scene.is_file():
        result["issues"].append("Missing editable source scene")
    if motion == "squat":
        # The current gates intentionally skip squat; skipping is not a pass.
        result["checks"]["currentProductionGate"] = "legacy_not_covered"
    else:
        for name, check in (
            ("collision", require_collision_pass),
            ("deformationAndVisualReview", require_deformation_pass),
        ):
            try:
                check(sex, motion, root=root)
            except (RuntimeError, OSError, ValueError, KeyError) as error:
                result["checks"][name] = "blocked"
                result["issues"].append(str(error))
            else:
                result["checks"][name] = "passed"

    receipt_path = folder / f"{motion}-media.json"
    receipt = read_json(receipt_path) if receipt_path.is_file() else {}
    if motion != "squat":
        provenance = (
            receipt.get("sceneSHA256") == result["sceneSHA256"]
            and result["sceneSHA256"] is not None
            and receipt.get("validatorSHA256")
            == sha256(Path(__file__).with_name("collision_audit.py"))
            and set(receipt.get("files", {}))
            == {f"{motion}.mp4", f"{motion}-poster.png"}
        )
        result["checks"]["mediaProvenance"] = "passed" if provenance else "blocked"
        if not provenance:
            result["issues"].append("Missing or stale scene-to-media receipt")

    total_bytes = 0
    for field, suffix in (("video", ".mp4"), ("poster", "-poster.png")):
        source = folder / f"{motion}{suffix}"
        name = bundled.get(field)
        # Catalog paths must be leaf names inside the App media directory.
        safe_name = isinstance(name, str) and name == Path(name).name
        target = root / "Repcendo/Resources/ExerciseAnimations" / name if safe_name else None
        ok = source.is_file() and target is not None and target.is_file()
        if ok:
            digest = sha256(source)
            ok = (
                source.stat().st_size > 0
                and sha256(target) == digest
                and bundled.get(f"{field}SHA256") == digest
                and (motion == "squat" or receipt.get("files", {}).get(source.name) == digest)
            )
            total_bytes += target.stat().st_size
        result["checks"][field] = "passed" if ok else "blocked"
        if not ok:
            result["issues"].append(f"Missing, changed or unverified {field}")
    result["bundledBytes"] = total_bytes
    result["status"] = (
        "blocked"
        if result["issues"]
        else "legacy_review_required" if motion == "squat" else "current_checks_passed"
    )
    return result


def inventory(root):
    catalog_path = root / "Repcendo/Resources/exercises.json"
    library = read_json(catalog_path)
    ids = [item["id"] for item in library]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate IDs in the exercise library")
    metadata = {**EXERCISES, **PLAN_EXERCISES, **LIBRARY_EXERCISES}
    implementations = {item["id"]: name for name, item in metadata.items()}
    if len(implementations) != len(metadata):
        raise ValueError("Multiple motion implementations claim the same dataset ID")
    catalog = read_json(root / "Repcendo/Resources/ExerciseAnimations/catalog.json")
    unknown = (set(implementations) | set(catalog)) - set(ids)
    if unknown:
        raise ValueError(f"Animation IDs absent from exercise library: {sorted(unknown)}")
    entries = []
    for item in sorted(library, key=lambda item: item["id"]):
        motion = implementations.get(item["id"])
        variants = (
            {
                sex: inspect_variant(
                    root, motion, sex,
                    catalog.get(item["id"], {}).get("variants", {}).get(sex, {}),
                )
                for sex in SEXES
            }
            if motion
            else {sex: {"status": "not_implemented"} for sex in SEXES}
        )
        statuses = {variant["status"] for variant in variants.values()}
        if not motion:
            status = "not_implemented"
        elif "blocked" in statuses:
            status = "blocked"
        elif "legacy_review_required" in statuses:
            status = "legacy_review_required"
        else:
            status = "current_checks_passed"
        entries.append({
            **item,
            "motion": motion,
            "status": status,
            "bundled": item["id"] in catalog,
            "variants": variants,
            "nextStep": {
                "not_implemented": "Specify motion, equipment and contacts; implement and review both characters",
                "blocked": "Repair the reported defect or stale evidence, then rerun checks and visual review",
                "legacy_review_required": "Bring the legacy scene under the current full-frame production checks",
                "current_checks_passed": "Reuse the exact reviewed scene and media; revalidate if changed",
            }[status],
        })
    by_equipment = []
    for equipment in sorted({item["equipment"] for item in entries}):
        selected = [item for item in entries if item["equipment"] == equipment]
        by_equipment.append({
            "equipment": equipment,
            "total": len(selected),
            "statuses": dict(sorted(Counter(item["status"] for item in selected).items())),
        })
    return {
        "schemaVersion": 1,
        "scope": "Every exercise ID in the current App text catalog, male and female",
        "catalogSHA256": sha256(catalog_path),
        "statusMeaning": "Current checks passed means existing engineering and visual evidence matches; not professional exercise certification. motionReferenceStatus distinguishes new reference checks from unchanged legacy scenes awaiting reference review. This worklist does not authorize export.",
        "summary": {
            "exerciseCount": len(entries),
            "requiredVariants": len(entries) * len(SEXES),
            "implementedExercises": len(implementations),
            "bundledExercises": len(catalog),
            "statuses": dict(sorted(Counter(item["status"] for item in entries).items())),
            "variantStatuses": dict(sorted(Counter(
                variant["status"] for item in entries for variant in item["variants"].values()
            ).items())),
        },
        "equipmentGroups": by_equipment,
        "exercises": entries,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/animation-library")
    args = parser.parse_args()
    report = inventory(args.root.resolve())
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "inventory.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    with (args.output / "inventory.csv").open("w", encoding="utf-8-sig", newline="") as file:
        fields = ["id", "name", "localizedName", "bodyPart", "equipment", "target", "motion", "status", "bundled", "nextStep"]
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(report["exercises"])
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
