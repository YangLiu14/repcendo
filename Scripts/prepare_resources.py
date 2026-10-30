#!/usr/bin/env python3
"""Build the text-only, offline catalog from the pinned dataset; no media is copied."""
import json
from pathlib import Path
from animation_samples.plan_exercises import PLAN_EXERCISES
from animation_samples.library_exercises import LIBRARY_EXERCISES

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/exercises-dataset"
DEST = ROOT / "Repcendo/Resources"
ALIASES = {
    "0025": "杠铃卧推", "0043": "杠铃深蹲", "0861": "坐姿绳索划船",
    "0405": "坐姿哑铃推举", "0085": "杠铃罗马尼亚硬拉", "2330": "高位下拉",
}

ALIASES.update({item["id"]: item["title"] for item in PLAN_EXERCISES.values()})
ALIASES.update({item["id"]: item["title"] for item in LIBRARY_EXERCISES.values()})

# The upstream hammer-curl text incorrectly switches to a supinated curl.
# Keep the pinned source intact; match the neutral-grip motion specification.
INSTRUCTION_OVERRIDES = {
    # The exact ID is unilateral; upstream instructions incorrectly say both arms.
    # https://www.muscleandstrength.com/exercises/one-arm-standing-hammer-curl.html
    "1671": [
        "站稳，单手持哑铃于身体一侧，掌心朝向身体，另一只手保持放松。",
        "保持躯干和上臂稳定，以中立握法屈肘举起哑铃，手腕与前臂对齐。",
        "接近肩部时短暂停留，然后有控制地下放，避免摆动躯干借力。",
        "完成一侧所需次数后换侧。",
    ],
    # Authored Zottman cycle uses the supinated starting position documented at
    # https://www.muscleandstrength.com/exercises/zottman-curl.html
    "0439": [
        "站稳，双手各持一个哑铃于身体两侧，掌心朝前，手腕与前臂对齐。",
        "保持上臂和躯干稳定，以掌心向上的握法屈肘举起哑铃。",
        "在顶部保持肘部位置，缓慢转动前臂，使掌心转向下方。",
        "保持反握，有控制地下放哑铃；回到底部后将掌心转回朝前，再开始下一次。",
    ],
    "0404": [
        "坐在有靠背的稳定长凳上，双脚平放地面，双手各持一个哑铃。",
        "将哑铃置于肩部两侧，保持掌心相对、手腕与前臂对齐。",
        "保持躯干稳定，向头顶推起哑铃，接近伸直时保留轻微屈肘。",
        "有控制地下放至肩部高度，全程保持中立握法。",
    ],
    "0313": [
        "站直，双手各持一个哑铃，手掌朝向躯干。",
        "保持上臂稳定、肘部位于身体两侧，整个动作中掌心相对，手腕与前臂对齐。",
        "屈肘将哑铃向肩部方向举起，不借助身体摆动。",
        "在顶部短暂停顿，然后有控制地将哑铃放回起始位置。",
        "重复所需的次数。",
    ],
    "0311": [
        "站稳，双手各持一个哑铃，手腕与前臂对齐。",
        "双臂在身体两侧略向前约 30 度的平面抬起，肘部保持轻微弯曲。",
        "保持拇指朝上，举至肩高，不耸肩或借助躯干摆动。",
        "有控制地下放，再重复动作。",
    ],
    "0392": [
        "坐在稳定的长凳上，双脚平放地面，双手各持哑铃于大腿外侧。",
        "保持躯干稳定，手腕与前臂对齐，将哑铃向前举起，掌心朝下。",
        "举至肩高后，有控制地下放至大腿外侧，为哑铃留出空间。",
        "重复所需的次数。",
    ],
    "0396": [
        "坐在稳定的长凳上，双脚平放地面，双手各持哑铃于大腿外侧。",
        "保持躯干稳定，肘部轻微弯曲，将哑铃向身体两侧举起。",
        "举至肩高，不耸肩；有控制地下放至大腿外侧。",
        "重复所需的次数。",
    ],
}


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    source = json.loads((SOURCE / "data/exercises.json").read_text())
    catalog = [dict(id=e["id"], name=e["name"], localizedName=ALIASES.get(e["id"]),
                    bodyPart=e["body_part"], equipment=e["equipment"], target=e["target"],
                    instructions=INSTRUCTION_OVERRIDES.get(e["id"]) or e["instruction_steps"].get("zh") or e["instruction_steps"]["en"])
               for e in source]
    assert len({e["id"] for e in catalog}) == len(catalog)
    (DEST / "exercises.json").write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")))
    (DEST / "DatasetLicense.txt").write_text((SOURCE / "LICENSE").read_text())
    (DEST / "example-plan.json").write_bytes((ROOT / "Examples/first-cycle.json").read_bytes())
    print(f"Prepared {len(catalog)} exercises (text only).")


if __name__ == "__main__":
    main()
