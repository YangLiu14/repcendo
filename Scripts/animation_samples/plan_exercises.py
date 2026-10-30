"""Explicit motion specifications for the four-day plan; separate from v2 samples."""


def entry(id, title, en, muscles, phases, **options):
    return dict(id=id, title=title, en=en, muscles=muscles, phases=phases, **options)


PLAN_EXERCISES = {
    "incline_press": entry(
        "0314",
        "上斜哑铃卧推",
        "INCLINE DUMBBELL PRESS",
        [("胸大肌", "上胸为主")],
        ["准备", "下放", "底部", "推起"],
    ),
    "pec_fly": entry(
        "0596", "蝴蝶机夹胸", "PEC DECK FLY", [("胸大肌", "胸部前侧")], ["准备", "合拢", "收缩", "回放"]
    ),
    "pushdown": entry(
        "0200",
        "绳索三头下压",
        "CABLE TRICEPS PUSHDOWN",
        [("肱三头肌", "上臂后侧")],
        ["准备", "下压", "伸展", "回放"],
    ),
    "cable_crunch": entry(
        "0175",
        "跪姿绳索卷腹",
        "KNEELING CABLE CRUNCH",
        [("腹直肌", "腹部前侧")],
        ["准备", "卷腹", "收缩", "回放"],
    ),
    "pulldown": entry(
        "2330", "高位下拉", "LAT PULLDOWN", [("背阔肌", "背部两侧")], ["准备", "下拉", "收缩", "回放"]
    ),
    "straight_pulldown": entry(
        "0238",
        "绳索直臂下拉",
        "STRAIGHT ARM PULLDOWN",
        [("背阔肌", "背部两侧")],
        ["准备", "下拉", "收缩", "回放"],
    ),
    "curl": entry(
        "0294",
        "哑铃弯举",
        "DUMBBELL BICEPS CURL",
        [("肱二头肌", "上臂前侧")],
        ["准备", "弯举", "收缩", "回放"],
    ),
    "leg_press": entry(
        "0739",
        "45度腿举",
        "45 DEGREE LEG PRESS",
        [("股四头肌", "大腿前侧"), ("臀大肌", "臀部后侧")],
        ["准备", "屈膝", "底部", "推起"],
    ),
    "rdl": entry(
        "0085",
        "杠铃罗马尼亚硬拉",
        "ROMANIAN DEADLIFT",
        [("腘绳肌", "大腿后侧"), ("臀大肌", "臀部后侧")],
        ["准备", "髋后移", "下放", "站起"],
    ),
    "leg_curl": entry(
        "0599", "坐姿腿弯举", "SEATED LEG CURL", [("腘绳肌", "大腿后侧")], ["准备", "屈膝", "收缩", "回放"]
    ),
    "leg_extension": entry(
        "0585",
        "坐姿腿屈伸",
        "SEATED LEG EXTENSION",
        [("股四头肌", "大腿前侧")],
        ["准备", "伸膝", "收缩", "回放"],
    ),
    "calf_raise": entry(
        "0605",
        "器械站姿提踵",
        "STANDING CALF RAISE",
        [("小腿后侧肌群", "以腓肠肌区域示意")],
        ["准备", "提踵", "顶端", "下放"],
    ),
    "shoulder_press": entry(
        "0405",
        "坐姿哑铃推举",
        "SEATED DUMBBELL PRESS",
        [("三角肌", "肩部前侧 / 外侧")],
        ["准备", "推举", "顶端", "下放"],
    ),
    "lateral_raise": entry(
        "0334",
        "哑铃侧平举",
        "DUMBBELL LATERAL RAISE",
        [("三角肌中束", "肩部外侧")],
        ["准备", "抬起", "顶端", "下放"],
    ),
    "reverse_fly": entry(
        "0602",
        "蝴蝶机反向飞鸟",
        "REVERSE PEC DECK FLY",
        [("三角肌后束", "肩部后侧"), ("上背肌群", "斜方肌区域示意")],
        ["准备", "展开", "收缩", "回放"],
    ),
    "reverse_crunch": entry(
        "0872",
        "反向卷腹",
        "REVERSE CRUNCH",
        [("腹直肌", "腹部前侧")],
        ["准备", "骨盆卷起", "收缩", "下放"],
        open_hands=True,
    ),
    "dead_bug": entry(
        "0276",
        "死虫式",
        "DEAD BUG",
        [("腹直肌 / 腹斜肌", "核心稳定区域")],
        ["左手右腿", "收回", "右手左腿", "收回"],
        open_hands=True,
        frames=192,
    ),
}

PLAN_MUSCLES = {
    "incline_press": ["pectoralis_major"],
    "pec_fly": ["pectoralis_major"],
    "pushdown": ["triceps_brachii"],
    "cable_crunch": ["rectus_abdominis"],
    "pulldown": ["latissimus_dorsi"],
    "straight_pulldown": ["latissimus_dorsi"],
    "curl": ["biceps_brachii"],
    "leg_press": ["quadriceps", "gluteus_maximus"],
    "rdl": ["hamstrings", "gluteus_maximus"],
    "leg_curl": ["hamstrings"],
    "leg_extension": ["quadriceps"],
    "calf_raise": ["gastrocnemius"],
    "shoulder_press": ["deltoid_anterior", "deltoid_lateral"],
    "lateral_raise": ["deltoid_lateral"],
    "reverse_fly": ["deltoid_posterior", "trapezius"],
    "reverse_crunch": ["rectus_abdominis"],
    "dead_bug": ["rectus_abdominis", "external_oblique"],
}
