#!/usr/bin/env python3
"""Bundle only Repcendo's original, reviewed exercise videos; never upstream GIFs."""
import hashlib
import json
import shutil
from pathlib import Path

from animation_samples.exercise_catalog import EXERCISES

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/animation-samples-v2"
DEST = ROOT / "Repcendo/Resources/ExerciseAnimations"


def main():
    catalog = json.loads((ROOT / "Repcendo/Resources/exercises.json").read_text())
    known_ids = {item["id"] for item in catalog}
    entries = {}
    copies = []
    for motion, metadata in EXERCISES.items():
        exercise_id = metadata["id"]
        assert exercise_id in known_ids and exercise_id not in entries
        variants = {}
        for sex in ("male", "female"):
            files = {}
            for field, suffix in (("video", ".mp4"), ("poster", "-poster.png")):
                source = SOURCE / sex / f"{motion}{suffix}"
                data = source.read_bytes()
                assert data, f"Empty asset: {source}"
                name = f"{exercise_id}-{sex}{suffix}"
                copies.append((source, DEST / name))
                files[field] = name
                files[f"{field}SHA256"] = hashlib.sha256(data).hexdigest()
            variants[sex] = files
        entries[exercise_id] = dict(title=metadata["title"], variants=variants)
    DEST.mkdir(parents=True, exist_ok=True)
    for source, destination in copies:
        shutil.copyfile(source, destination)
    (DEST / "catalog.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
    print(f"Bundled {len(entries)} original motions / {len(copies) // 2} videos with posters.")


if __name__ == "__main__":
    main()
