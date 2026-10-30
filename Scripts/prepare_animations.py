#!/usr/bin/env python3
"""Bundle only Repcendo's original, reviewed exercise videos; never upstream GIFs."""
import hashlib
import json
import shutil
from pathlib import Path

from animation_samples.exercise_catalog import EXERCISES
from animation_samples.plan_exercises import PLAN_EXERCISES
from animation_samples.collision_gate import require_media_pass

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/animation-samples-v2"
DEST = ROOT / "Repcendo/Resources/ExerciseAnimations"


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library-batch", help="Sync only an independently reviewed full-library batch")
    args = parser.parse_args()
    if args.library_batch:
        from animation_samples.library_exercises import LIBRARY_EXERCISES
        # Delivery tools also support direct script execution from their folder.
        import sys
        sys.path.insert(0, str(ROOT / "Scripts/animation_samples"))
        from library_delivery import sync
        names = [n for n, c in LIBRARY_EXERCISES.items() if c["batch"] == args.library_batch]
        if not names:
            parser.error("Unknown or empty library batch")
        sync(names)
        print(f"Bundled {len(names)} reviewed library motions; preserved existing entries.")
        return
    require_media_pass()
    catalog = json.loads((ROOT / "Repcendo/Resources/exercises.json").read_text())
    known_ids = {item["id"] for item in catalog}
    entries = {}
    copies = []
    # Full legacy rebuilds must also retain already delivered library batches.
    # Validate their current sources before copying or replacing the catalog.
    current_path = DEST / "catalog.json"
    if current_path.exists():
        import sys
        sys.path.insert(0, str(ROOT / "Scripts/animation_samples"))
        from library_exercises import LIBRARY_EXERCISES
        from library_delivery import collect_entries
        current = json.loads(current_path.read_text())
        names = [n for n, c in LIBRARY_EXERCISES.items() if c["id"] in current]
        library_entries, library_copies = collect_entries(names)
        entries.update(library_entries)
        copies.extend(library_copies)
    for motion, metadata in {**EXERCISES, **PLAN_EXERCISES}.items():
        source_folder = (
            SOURCE if motion in EXERCISES else ROOT / "docs/animation-plan-v3"
        )
        exercise_id = metadata["id"]
        assert exercise_id in known_ids and exercise_id not in entries
        variants = {}
        for sex in ("male", "female"):
            files = {}
            for field, suffix in (("video", ".mp4"), ("poster", "-poster.png")):
                source = source_folder / sex / f"{motion}{suffix}"
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
    (DEST / "catalog.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        f"Bundled {len(entries)} original motions / {len(copies) // 2} videos with posters."
    )


if __name__ == "__main__":
    main()
