"""Shared display metadata and primary muscle selections for supported motions.

Adding an entry also requires a motion/equipment implementation and its checks.
"""

EXERCISES = {
    "squat": dict(
        number="01",
        title="杠铃深蹲",
        en="BARBELL BACK SQUAT",
        id="0043",
        muscles=[("股四头肌", "大腿前侧"), ("臀大肌", "臀部后侧")],
        phases=["准备", "下蹲", "底部", "站起"],
    ),
    "bench": dict(
        number="02",
        title="杠铃卧推",
        en="BARBELL BENCH PRESS",
        id="0025",
        muscles=[("胸大肌", "胸部前侧")],
        phases=["准备", "下放", "底部", "推起"],
    ),
    "row": dict(
        number="03",
        title="坐姿绳索划船",
        en="SEATED CABLE ROW",
        id="0861",
        muscles=[("背阔肌", "背部两侧"), ("斜方肌区域", "肩胛间表面位置")],
        phases=["准备", "拉回", "收缩位", "回放"],
    ),
}

PRIMARY_MUSCLES = {
    "squat": ["quadriceps", "gluteus_maximus"],
    "bench": ["pectoralis_major"],
    "row": ["latissimus_dorsi", "trapezius"],
}
