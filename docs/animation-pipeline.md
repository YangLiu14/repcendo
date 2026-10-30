# 原创动作动画制作流水线

原三动作流程制作深蹲、卧推和坐姿划船，男女各一版。本文后半部分说明当前 19 动作流程与形变门禁。原三动作入口为 `Scripts/animation_samples/pipeline.py`。新增动作可以复用人物、骨架、肌群、渲染和交付步骤，但运动轨迹与接触约束仍需实现、校准和目视审核；当前不是输入动作名称就自动生成正确动画的系统。

## 原三动作入口（历史）

生产环境为 macOS、Blender 5.2.1 LTS、Python 3 + Pillow、ffmpeg/ffprobe。Blender 自带 Python 负责 `bpy` 与 NumPy；外部 Python 负责批处理和 Pillow 排版。三个命令行程序必须在 PATH 中。中文卡片当前依赖系统的 Hiragino Sans GB 与 Arial 字体。

在项目根目录运行（`python3` 应选用安装了 Pillow 的解释器）：

```sh
# 查看阶段和命令，不修改文件
python3 Scripts/animation_samples/pipeline.py --dry-run

# 完整重建当前全部三个动作、男女版本、模型与验证结果
python3 Scripts/animation_samples/pipeline.py --mode full

# 验证已有结果，不重新渲染或打包
python3 Scripts/animation_samples/pipeline.py --mode verify
```

该入口记录原三动作制作方式。当前卧推/划船已纳入 19 动作形变门禁，应使用本文后面的 `plan_pipeline.py --prepare-review` / `--from-scenes` 流程；旧 `full` 不能跳过新审核要求。`full` 会更新现有 v2 成品目录。`verify` 需要本地渲染中间帧；这些位于忽略的 `build/`，新 checkout 应先运行 `full`。执行前会检查工具、输入文件和字体，阶段失败即停止。每次运行的阶段状态、命令与日志位于 `build/animation-pipeline/<UTC 时间>/`。运行成功只代表自动检查通过，不代表专业动作审核通过。

单个动作的快速迭代继续使用底层入口：

```sh
# 烘焙动作并输出关键姿势（会更新对应 Blender 场景）
python3 Scripts/animation_samples/render_sculpture_samples.py \
  --exercise squat --sex male --previews-only

# 只重渲染这个动作的男女版本
python3 Scripts/animation_samples/render_sculpture_samples.py --exercise squat
```

预览模式不是隔离沙盒，可能使对应 `.blend` 比旧视频更新。确认预览后应跑完整流水线，使场景、视频和报告对应同一版本。

## 阶段与代码

| 阶段 | 输入与工作 | 实现 / 输出 |
|---|---|---|
| 人物准备 | 读取选定雕塑；校准手脚、五指权重、肩颈形体；保留源档 | `character_assets/hand_rig.py`、`shoulder_rig.py` |
| 动作与器械 | 求解髋、四肢、手腕、接触目标；建模器械；烘焙 121 帧 | `animation_samples/build_sculpture_scene.py` |
| 渲染 | 两个有限并发 worker；动作与正背面肌群参考 | `render_sculpture_samples.py` |
| 接触近景 | 检查实际握持、肩颈与落杠；正/背/侧视角 | `render_hand_closeups.py`、`render_squat_review.py` |
| 独立人物导出 | 53 骨骼、五指张合、可编辑肌群开关 | `character_assets/export_hand_rig.py` → Blender / GLB |
| 打包 | 中文卡片、海报、MP4、GIF、预览页和文件校验和 | `package_sculpture_samples.py` |
| 验证 | 真实网格接触、循环、脚底稳定、媒体、GLB 重导入 | 五个 `verify_*` 阶段 |
| 目视审核 | 正背侧轮廓、关节、运动方向、器械支撑和肌群展示 | 预览页与源场景；确认后才可进入 App 资源制作 |

相对于 `Scripts/` 的路径如表所示。动作标题、数据集 ID、阶段文案和主要肌群集中在 `animation_samples/exercise_catalog.py`。几何轨迹仍在现有场景生成器中，尚未抽成通用动作插件。

## 输入与交付约定

- 固定输入：`docs/character-assets/muscle-overlay-v1/{male,female}/greek-*-muscles.blend`；原始人物、UV、肌群材质和身体骨架作为来源，制作副本中应用已验证的修正。
- 新人物的上游流程仍是：概念图 → Tripo 网格 → 人体绑骨 → 局部几何与蒙皮校正。它是角色制作阶段，不需要为每个新动作重复调用 Tripo。
- 当前归一化人物约 0.98 模型单位高，X 向前、Y 向左、Z 向上。动画中转换到约真人尺度，世界 Y 向前、Z 向上。
- 每段 5 秒、24 fps。1–120 帧播放；121 帧只用于验证闭环。1 帧为准备姿势，61 帧为最低点或收缩位置。
- `docs/animation-samples-v2/` 保存 MP4、GIF、Blender 场景、近景、报告和预览页面；`docs/character-assets/hand-rig-v1/` 保存可复用骨架副本。
- `build/` 保存原始帧、排版中间帧和日志，不提交。最终资产与验证报告提交到 Git。历史截图和肩部修正前图是审查记录，不会自动重建。
- 当前媒体已通过 `Scripts/prepare_animations.py` 接入 iOS 离线资源；原深蹲保留旧版本，19 个计划动作走下述形变门禁。

## 扩展一个新动作

1. **写清动作规格。** 确认名称与数据集 ID、器械、动作阶段、活动范围、主要显示肌群和正背侧参考。使用有许可的参考或原创动作，不复制来源不明的 GIF。
2. **选择现有运动模式。** 深蹲可提供固定足底与髋膝链参考；卧推可提供仰卧支撑与推举轨迹参考；划船可提供坐姿支撑、握把与绳索参考。相似动作也需重新检查角度、接触和肌群，不应仅改标题或器械外观。
3. **实现动作与器械。** 在场景生成器中新增明确分支，定义身体轨迹、手腕方向、接触点、器械跟随、相机及活动范围，然后注册元数据。只添加 catalog 项目不会自动获得正确运动求解。
4. **先出关键姿势。** 检查准备、中间、终点和回程；同时看正面、背面、侧面。优先解决错误扭转、浮空、身体/器械穿模和脚滑，再渲染全片。
5. **增加该动作的接触验证。** 实际蒙皮应参与检查。根据动作检查手/握把、肩/杠铃、背/靠垫、脚/地面或踏板等；不要只比较骨骼目标位置。
6. **接入批处理与验证列表。** 当前验证脚本仍明确枚举这三个动作，需给新动作补充采样、器械坐标系和约束，再纳入流水线。新身体、不同杆径或新握法也要重新校准。
7. **完整制作、审核、交付。** 保留原场景、参数、验证结果、版本和校验和；确认男女版本都合理，再作为独立资产导入 App。

随着动作增加，下一步适合抽出 `MotionAdapter`（人体轨迹）、`Equipment`（器械及坐标）、`ContactCheck`（接触检查）三个接口。现在保留三个已经跑通的具体实现，避免把尚未验证的动作假设藏进通用配置。

## 本轮经验与自动检查的边界

| 已发生的问题 | 为什么旧检查漏掉 | 已补充的检查 |
|---|---|---|
| 手没有握杆 | 手掌参考点正确，但没有逐指骨骼 | 30 根指骨实际带动蒙皮；杆周围包覆、各指接近杆面、相对器械滑移 |
| 杠铃穿肩 | 固定偏移和握点无法证明躯干接触正确 | 变形网格的杠轴表面/轴心检测、三向射线体内判断、双侧上背间隙 |
| 颈后隆起、肩部扭曲 | 原始形体、错误权重和不稳定上臂旋转叠加 | 颈后网格相对躯干的偏移；正/背/侧面轮廓对照 |
| 脚底随腿形变漂移 | 固定踝骨不等于固定脚底网格 | 实际足底顶点的世界坐标漂移 |
| 媒体截边或模型导出失效 | 渲染成功不代表交付可用 | 720 帧透明边界、完整媒体解码、GLB 重导入及指骨形变 |

现有报告覆盖本轮设置的采样和约束，不是全身通用碰撞或生物力学正确性的证明。五指目前是 FK；肌群为体表近似区域，衣物折痕也会保留。专业动作审核和目视检查仍是必要的质量步骤。

## 穿模检测与 19 动作生产流程

新增 `Scripts/animation_samples/plan_pipeline.py`，将检测作为渲染、打包和 App 资源同步的前置条件。使用带 Pillow 的 Python：

```sh
python Scripts/animation_samples/plan_pipeline.py --prepare-review
# 查看生成的三视角证据，记录审核决定后（不得自动批准）：
# 已在 Blender 中调整过场景，保留编辑结果：
python Scripts/animation_samples/plan_pipeline.py --from-scenes
```

顺序：烘焙 19 动作的男女场景 → 检测器回归测试 → 全帧穿模检测 → 全帧形变检查 → 三视角审核 → 渲染 → 握持/循环/支撑检查 → 视频打包 → App 同步 → 资源完整性检查。`--dry-run` 仅打印步骤。原有深蹲不属于本次计划的 19 个动作，仍保留原资源。

### 检测覆盖

- 在最终变形后的网格上检查，包含骨骼、握持形态修正、关节修正和垫面接触修正；不能用骨骼距离代替皮肤表面。
- 双向检查人物进入器械、器械进入人物。器械长边按 12 mm 间隔细分采样，避免细杠杆两端都在体外时漏检。
- 对非局部身体表面进行三角形相交检查，包括双侧肢体、手/前臂与躯干、头部等。共用顶点、同一解剖表面，以及原始模型中相距不足 14 cm 的相邻关节连接区域不作为独立碰撞体。指间和局部皮肤褶皱仍需近景目视审核。
- 穿透容差固定为 2 mm，不允许为某个失败器械整体放行。自碰撞的深度是相交面片的平面侵入量，用于定位和阻断，不是物理软组织压力。
- 正式检测覆盖每个输出帧和额外的循环闭合帧；死虫式完整覆盖两侧。离散帧检查不代表连续物理仿真。

```sh
# 快速诊断，不能用来授权导出
python Scripts/animation_samples/validate_collisions.py --frames key
# 指定动作重新检查；默认就是全部帧
python Scripts/animation_samples/validate_collisions.py --exercise leg_press
# 全部 38 个场景
python Scripts/animation_samples/validate_collisions.py
```

失败报告记录性别、动作、帧、器械、身体区域、位置、侵入量和交叠面片。诊断文件在 `build/collision-audit/`；正式证据在 `docs/animation-plan-v3/collision-validation.json`。修改场景或检测器后，旧报告自动失效。未完成全部帧、存在失败项、哈希不符或缺少报告时，渲染和打包必须停止。

### 几何修复原则

`fit_contacts.py` 用整个循环的实际皮肤表面设置静态坐垫/靠垫，避免垫子跟随皮肤抖动；踏板和滚垫按实际运动接触面设置轨迹。握把连接杆从握持区以外的端部接出。旧 `joint_correctives.py` 的强普通 Smooth 已删除。现在使用共享绑定校准、父级坐标系下的旋转、前臂扭转辅助骨骼和原生 Preserve Volume；接触形态修正仍接受同样的检测。不能隐藏器械、删除身体面片、扩大检测豁免范围或更改训练计划来消除报错。

检查通过后还需查看主镜头及侧面关键姿势：手是否包住握把、器械是否有支撑、轨迹是否符合动作、皮肤修正是否造成塌陷或鼓包。`*-media.json` 将视频/封面哈希与已通过检测的场景绑定；`prepare_animations.py` 会拒绝来自旧场景的视频。


## 人物形变流程 v2（2026-10-29）

`character_assets/prepare_athlete.py` 是当前 19 动作与独立关节测试的同一入口。原人物、UV 与肌群来源保留；制作副本增加 4 根前臂扭转辅助骨，共 57 根骨骼。独立中性资产和测试片位于 `docs/character-assets/deformation-rig-v2/`。旧 `hand-rig-v1` 导出是历史 53 骨版本，不能当作新绑定。

1. 校准脚踝/脚趾旋转中心及局部权重，限制足骨对小腿的拖拽；肘膝按关节中心分配相邻骨骼影响。
2. 肩、上臂、前臂使用父级传递的旋转参考；握持方向产生的轴向转动分布到前臂辅助骨。自由手不使用虚构器械握点。
3. Blender Armature 开启 Preserve Volume（双四元数蒙皮）。接触修正的逆映射与其一致，并用实际求值网格验证误差；不使用普通强平滑掩盖折叠。
4. `joint_stress.py` 生成肘、前臂、肩、髋、膝、踝、趾的独立活动测试。极端测试角度是查错输入，不是训练动作范围建议。
5. `validate_deformations.py` 检查完整循环的权重归一化、异常骨缩放、相邻帧旋转跳变、肘部额外轴转、脚骨影响范围和强平滑回归。网格边长变化仅标记可疑帧，不据此证明解剖正确。
6. `render_deformation_review.py` 输出正/侧/背关键帧与可疑帧；`compose_deformation_review.py` 只生成 pending 记录。实际查看后才可在 `deformation-visual-review.json` 写入 accepted、审核说明与对应图片哈希。器械在该人体形变视图中暂时隐藏；完整场景碰撞审查独立保留。
7. `deformation_gate.py` 要求自动检查与目视证据同时对应当前场景哈希。缺少、过期或失败时，正式渲染、打包、App 同步停止。

隔离制作可给 `render_plan.py` 传 `--output-root build/候选目录`，给两个 validator 和形变 review 脚本传 `--root build/候选目录`。输入角色仍来自仓库，输出不会覆盖已交付文件。只有检查/审核通过的候选场景、报告和证据才可推广；场景重新烘焙后必须重新检查。

本轮接受的是当前 19 动作范围内的示意画面。原雕塑的衣褶、腋下折痕与极端膝踝姿态的局部形状仍存在；这不是肌肉/软组织物理模拟，也不是专业动作审核。新动作超出现有范围时需重新做关节与多视角检查，必要时重拓扑或制作姿态修正形态。

独立关节基线可以单独生成，不改动作成品：

```sh
blender -b --python-exit-code 1 --python Scripts/character_assets/joint_stress.py -- --sex male --output-root build/rig-review --render
blender -b --python-exit-code 1 --python Scripts/character_assets/joint_stress.py -- --sex female --output-root build/rig-review --render
```

接触逆映射的保留厚度模式还检查左右 Shape Key 独立性；旧硬投影配方只为已验收动作兼容保留。新增握持动作优先试用保留厚度模式，但仍须检查每指接近杆面，不能通过扩大间隙换取碰撞通过。

### 握持方向与手腕约束

表面包覆检查回答“握住了吗”，不能回答“握反了吗”。卷腹增加 `verify_grip_orientation.py` 全 121 帧动作专用检查：两掌向内、拳头食指端朝上、轴转和折腕角度。此步骤放在形变检查之后、视觉审核之前；`deformation_gate.py` 在正式渲染、打包和 App 同步时强制检查报告、全帧覆盖、场景/检测器哈希及指标。

```sh
blender -b --python-exit-code 1 --python Scripts/animation_samples/verify_grip_orientation.py
# 隔离输出可用 -- --root build/候选目录；--frames 61 仅诊断，不写生产报告。
```

`render_deformation_review.py` 为卷腹额外输出器械可见的四阶段手部近景；`compose_deformation_review.py` 将其纳入审核证据。两者支持 `--exercise cable_crunch`，但不会自动批准。`verify_plan_grips.py` / `verify_plan_scenes.py` 的同名选项生成带动作名的独立报告，避免部分审查覆盖全部结果。其他动作后续应按正握、反握、中立握等明确各自语义，不能套用卷腹阈值。


### 死虫式肩腋姿态修正

`bake_shoulder_correctives.py` 在原 Armature / Preserve Volume 后增加局部姿态修正 Shape Keys。原网格、UV、骨架和手脚轨迹保留；不是替换蒙皮算法，也不宣称已经修好角色在所有动作下的肩部绑定。

- `shoulder_volume.py` 对肩腋局部执行保形表面求解，并用躯干、上臂体积引导避免单纯平滑导致上臂塌陷。男女分别校准；女性前肩衣褶另有随抬臂相位渐变的保护区域。
- 每 8 帧求解一个姿态，周期插值后将 Shape Key 权重逐帧烘焙。通过与 DQ 蒙皮一致的逆映射写回形态；不改变原骨长或动画。缓存绑定未修正场景、求解器、逆映射代码及 Blender 版本。
- 对插值后的每帧实际皮肤再做局部肩腋接触修正。修正位移过大或不收敛则失败。独立穿模检测仍使用原来的 2 mm 容差；没有扩大检测豁免范围。
- `diagnose_torso_strain.py --all-frames` 检查全部 193 帧（含闭环帧），肩腋区域边长拉伸 p95 必须 ≤1.8。这是针对已知缺陷的回归阈值，不是人体生理标准。`deformation_gate.py` 同时核对完整帧覆盖、场景及检测器哈希。
- 仍需全循环形变/穿模检查、网格闭环检查、正侧背视图与 `dead_bug-shoulders.jpg` 近景的实际审核。单靠边长变小不能验收：塌陷也会让指标变小。局部雕塑折痕及衣褶仍会存在。

该配方只支持当前两个人物和 192 帧死虫式循环。新人物、拓扑或抬臂轨迹必须重新校准；不能直接用于其余动作。

Blender 5.2 / Python 3.13 的求解阶段需要 SciPy。Apple Silicon 开发环境可安装到被忽略的项目目录，不修改 Blender 应用：

```sh
python3 -m pip install --target build/deformation-python --no-deps --only-binary=:all: \
  --platform macosx_14_0_arm64 --implementation cp --python-version 3.13 --abi cp313 scipy==1.18.1
# 其他平台应匹配 Blender 自带 Python 的 ABI/架构；可用 REPCENDO_DEFORMATION_MODULES 指定安装目录。
python3 Scripts/animation_samples/render_plan.py --bake-only --exercise dead_bug --output-root build/dead-bug-candidate
# render_plan 的新烘焙会自动执行姿态修正及逐帧拉伸检查。
# 手工修改已有场景后，先重新运行逐帧拉伸检查，再进入原有 audit / review / render 流程：
blender -b --python-exit-code 1 --python Scripts/animation_samples/diagnose_torso_strain.py -- \
  --scene build/dead-bug-candidate/docs/animation-plan-v3/male/dead_bug.blend \
  --all-frames --output build/dead-bug-candidate/docs/animation-plan-v3/male/dead_bug-strain.json
```

直接调用修正脚本时必须输入未修正的场景；存在 Shape Keys 时会拒绝重复烘焙。`*-shoulder-corrective.json` 记录制作来源；发布仍由独立检查和视觉审核决定。

## 完整动作库分批制作（2026-10-29 起）

目标为 App 文本库的 1,324 个精确动作 ID、男女各一版。`docs/animation-library/inventory.json` / `inventory.csv` 是可重新生成的制作清单，不是成品覆盖声明。`library_exercises.py` 只注册已编写独立规格和适配器的动作；未实现项目不能按相似名称套用现有视频。

新批次放在 `docs/animation-library/`，不会覆盖原三动作和计划动作目录。共用人物准备、骨长约束、前臂扭转及原来的实际网格碰撞/形变检测引擎。每个新动作还需完整循环的握持语义、逐指接触、足底稳定和网格闭环检查。第 001 批实现中立握的站姿/坐姿锤式弯举、旋后握的左右交替弯举、正握前平举；交替动作包含左右完整循环。

```sh
# python 选用带 Pillow 的解释器；Blender / ffmpeg / ffprobe 仍需在 PATH。
python Scripts/animation_samples/library_pipeline.py bake --batch 001
python Scripts/animation_samples/library_pipeline.py audit --batch 001
python Scripts/animation_samples/library_pipeline.py review --batch 001
python Scripts/animation_samples/library_pipeline.py compose --batch 001
# 实际查看每个 *-review.jpg，记录到同名 *-review.json。
# 自动生成器只写 *-review-pending.json，不会自动批准。
python Scripts/animation_samples/library_pipeline.py render --batch 001
python Scripts/animation_samples/library_pipeline.py references --batch 001
python Scripts/animation_samples/library_pipeline.py package --batch 001
python Scripts/prepare_resources.py
python Scripts/prepare_animations.py --library-batch 001
python Scripts/animation_samples/library_pipeline.py page --batch 001
python Scripts/animation_samples/library_inventory.py
```

每阶段支持 `--exercises` 指定动作，制作/检查阶段还支持 `--sex`；每次最多两个 worker；跨进程文件锁保证同一工作目录最多两个 Blender 子进程，同一动作/性别的制作阶段串行。`--root` 用于隔离候选。视频断点续作绑定场景 SHA-256，场景变化时只清除该动作的旧渲染帧。正式打包前检查全部 alpha 边界，编码后完整解码并核对尺寸、帧数及媒体来源。每项报告独立保存，缺少、过期、失败或被撤回的视觉证据均拒绝输出。

`prepare_animations.py --library-batch` 先检查选中批次男女两版的全部证据，再加入该批次媒体；其他现有文件与目录项保留。该命令不会自动重审或放行其他动作；旧版深蹲仍单独标记，死虫式现已通过肩腋专项修复和重新验收。原默认 `prepare_animations.py` 保留旧流程的整体门禁。

原始帧、诊断和日志在忽略的 `build/animation-library/`；已验收源场景、视频、封面和报告在 `docs/animation-library/`。制作全库应逐批完成，避免将数十万原始帧同时留在磁盘；未经复验不得清理正在制作批次的帧。

第 002 批新增 1648、1677、0392、0387、0396、0429、0311、0335；使用同一命令将 `--batch` 改为 `002`。全帧检查增加闲置侧手臂稳定、峰值动作幅度、full-can 拇指方向与肩胛平面，以及侧举/前举阶段的实际方向。`audit --frames 1,31,61,91,121` 可生成关键帧诊断，但不能用于正式发布。检查器更新后必须重跑此前批次的实际场景和媒体校验。预览按批次筛选，男女视频均使用内容哈希刷新缓存。


第 003 批使用 `--batch 003`，新增 0289、0352、0321、3545、0388、0404、0426、0427。平凳、45° 上斜、坐姿和站姿分别建模；中立握保持掌心相对，交替推举包含左右完整循环。0404 上游文字的掌向错误由 `prepare_resources.py` 中的显式覆盖修正，不改上游子模块。

推举的独立检查入口为 `library_scene_v3.py` / `library_audit_v3.py`，通过规格的 `audit_version=3` 选择，并将动作规格摘要绑定到检查报告与媒体收据。原批次仍使用原检查器；共享碰撞/形变引擎变化时，所有受影响的报告仍必须真实重查。v3 检查实际腕肘对齐、推举顶部范围、闲置侧稳定、每指握杆表面、靠垫的实际承重蒙皮间距、脚部稳定和闭环。平卧额外分别检查上背与后脑支撑，避免仅用臀部最低点通过。`audit --frames key` 检查九个关键帧，仅输出 build 中的诊断报告，不能替代全帧检查或视觉验收。

第 004 批使用 `--batch 004`，对应 0315、0320、0298、0439、0414、0415、0406、0293，采用独立 `library_scene_v4.py` / `library_audit_v4.py`，保留旧版检查器。上斜弯举检查靠背/坐垫承重间距和上臂垂直悬垂；跨体锤式检查交替、跨中线趋势和拇指端方向；佐特曼检查旋后举起、顶部旋前、旋前下放及底部复位，连续帧仍执行旋转跳变检查；耸肩检查直臂、肩部位移和躯干稳定；俯身划船检查固定髋铰链与肘部后拉。所有项目继续使用实际蒙皮、双向器械穿入和非邻接自交检查，容差保持 2 mm。

佐特曼的四阶段不是等时长，`phase_ends=(0.375, 0.5, 0.875, 1.0)` 将视频阶段文字与 8 秒动作对齐；顶部/底部转腕额外加入多视角审核帧。不能只以顶部与底部姿势正确证明翻腕连续。旧失败样本保留在 `build/animation-library/batch-004-diagnostics/`。

## 器械照片参考与机构验收（2026-10-30）

新增或修订器械先执行 [照片参考流程](equipment-references/README.md)，把实际查看的产品照片和结构观察记入 `docs/equipment-references/`。照片结构审核独立于人体形变和穿模检查。

蝴蝶机夹胸/反向飞鸟共用 `pec_deck.py`：参照 SS-FLY 的顶部双竖直转轴、横向摆臂、下垂握臂、胸背垫、座椅和配重塔。拳心沿固定半径圆弧，手臂 IK 匹配握把；杆件保持定长。男女分别适配静态握把高度与臂长，行程中不伸缩。女性使用保留指厚的握持修形，男性保留经全循环验证的既有接触配方。

`verify_pec_deck.py` 检查每版全 121 帧的固定转轴、杆长、连接点和竖直握把，并绑定参考记录/检测器/场景哈希。`render_pec_deck_review.py` / `compose_pec_deck_review.py` 生成器械可见的主镜头、侧面三阶段证据；与人体正侧背图一起实际查看后，将设备图片哈希加入视觉审核记录。形变门禁同时要求该机构检查和设备图片；旧的伸缩斜杆场景会被拒绝。上述命令均支持隔离 `--root`，并已接入 `plan_pipeline.py --prepare-review`。

此器械是保留结构和运动原理的简化示意模型，未复刻厂家全部传动零件或尺寸。其他旧器械仍需逐项补做照片审核，不能因本次四个场景验收而认为它们已通过。

### 全器械照片复核与更新

现有资产的照片索引见 `docs/equipment-references/README.md` 和 `equipment-audit.json`。`equipment_refit.py` 在接触拟合后补齐承力架及传动，不修改人物。覆盖高低位绳索、腿机、提踵机、腿举和 8 种带靠背的训练凳动作。

`verify_equipment_refit.py -- --root <候选目录> --before <原场景目录>` 检查每一帧固定架、连杆长度、导轨方向、配重与绳长关系，并比较前后人物网格。`render_equipment_review.py` / `compose_equipment_review.py` 输出主、侧镜头三姿势图片；必须实际查看再写 `equipment-visual-review.json`。`equipment_gate.py` 同时用于计划和新增动作库的发布检查。

人体每帧网格完全一致时，可以保留旧人体多视角证据，但必须记录原场景摘要、完整循环人体摘要和比较证明，并附上新的器械图；不能把旧图当作新器械验收。任何人体改变仍需重新制作人体证据。新器械仍必须跑原有碰撞/形变/动作检查，未经完整验收不替换成品。


### 第 005 批：单臂动作与新握持配方

第 005 批对应 1670、1671、0425、0355、0361、0424、0343、1281，使用 v5 独立动作检查。每段演示左臂一个循环，空闲手张开放松且没有哑铃，文案提示完成一侧后换侧；它不是左右交替动作。三种弯举分别验证旋后、中立、旋前握法；侧平举及三种方向的推举按实际骨骼与蒙皮核验活动范围。

新场景优先采用 `contact_recipe="preserve_thickness"` 的双四元数逆映射握持修形，空闲手的器械接触 Shape Key 设为零。对全部输出帧重新检查每指接近杆面、手腕方向和相对滑移，再查看手部近景，不因采用新配方自动通过。当前照片记录为 `equipment-references/batch-005.json`，其摘要也进入 v5 检查与媒体收据。

平凳纵梁在坐垫接触拟合之后连接垫底，不能使用原始固定高度穿入人物。上斜凳继续通过 `equipment_refit.py` 补齐背撑，并由 `verify_equipment_refit.py -- --exercise single_incline_press` 检查完整循环。主、侧准备/中间/最大行程图均包含在本批五视角证据中，实际比较照片后才记录器械通过。每版重新制作人体证据，不复用旧人体截图。

验证命令仍使用 `library_pipeline.py ... --batch 005`。`test_unilateral_scenes.py` 在内存中制造握反、双侧负重、空闲臂随动、哑铃伸缩、凳面漂移和错误支撑的真实场景反例；不修改交付场景。保留原碰撞与形变检测器，穿透容差仍为 2 mm。
