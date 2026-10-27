#!/usr/bin/env python3
"""Build the text-only, offline catalog from the pinned dataset; no media is copied."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/exercises-dataset"
DEST = ROOT / "Repcendo/Resources"
ALIASES = {
    "0025": "杠铃卧推", "0043": "杠铃深蹲", "0861": "坐姿绳索划船",
    "0405": "坐姿哑铃推举", "0085": "杠铃罗马尼亚硬拉", "2330": "高位下拉",
}


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    source = json.loads((SOURCE / "data/exercises.json").read_text())
    catalog = [dict(id=e["id"], name=e["name"], localizedName=ALIASES.get(e["id"]),
                    bodyPart=e["body_part"], equipment=e["equipment"], target=e["target"],
                    instructions=e["instruction_steps"].get("zh") or e["instruction_steps"]["en"])
               for e in source]
    assert len({e["id"] for e in catalog}) == len(catalog)
    (DEST / "exercises.json").write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")))
    (DEST / "DatasetLicense.txt").write_text((SOURCE / "LICENSE").read_text())
    (DEST / "example-plan.json").write_bytes((ROOT / "Examples/first-cycle.json").read_bytes())
    print(f"Prepared {len(catalog)} exercises (text only).")


if __name__ == "__main__":
    main()
