# 实现发现

- 仓库初始只有 README 和刚加入的 exercises-dataset submodule，无 AGENTS.md。
- 数据集固定在 7455efae41b330c265e7cd4b78dfa848e7ce5ebd；1,324 个动作，中文步骤齐全。
- 上游 LICENSE 将图像/GIF 排除在 MIT 之外。本版只打包文字数据和许可说明，媒体接入留到获得授权以后。
- 本机 Xcode 27.1 已安装；用户已接受许可。可使用 iOS 26.3 模拟器；xcodegen 不存在。
- UI 技能初次设计搜索偏营销站，不能照搬。采用原生 SF 字体、语义背景色、橙色强调和明确的触控目标；不采用网页 hero/hover/游戏化建议。
- Apple fileImporter 文档要求对外部文件使用配对的 security-scoped access。导入后只存储解码后的值。
  https://developer.apple.com/documentation/swiftui/view/fileimporter(ispresented:allowedcontenttypes:oncompletion:)

## 产品边界
- 用户有三年健身经验，第一版自用；痛点是固定计划缺少递进、第三方工具不允许自由定制。
- 采用完整周期计划，周间目标可变化；没有日期绑定，可按实际生活安排训练。
- 重量单位固定 kg；第一版以次数型力量训练为主。

## 验证发现
- XCTest 在模态关闭动画中能看到底部标签，但不能点击；需等待 hittable，而非只检查 exists。
- iOS 26 文件导出界面提供「保存」，此位置没有「取消」；端到端测试实际保存文件后继续。
- `-AppleInterfaceStyle Dark` 未改变截图主题；深色验证应使用 simctl ui appearance，而非依赖启动参数。
- 次要文字实色对比度：浅色约 6.13:1，深色约 9.6:1；强调色分别约 6.16:1 与 10.82:1。

## 原创动作动画
- 本机 Blender 5.2.1 LTS 与 ffmpeg 可用；本会话无 Blender MCP 工具，9876 无监听。采用本地 Blender Python，不依赖 MCP。
- 程序化原创人物、器械、动画与肌群位置示意；不读取或改绘上游媒体。
- 标记范围：深蹲股四头肌/臀大肌；卧推胸大肌；窄握坐姿划船背阔肌/肩胛间区域（菱形肌与中斜方肌区域，示意不表示解剖分层）。
- 参考（仅文本知识，不复制图片）：https://www.acefitness.org/continuing-education/certified/november-2019/7403/understanding-the-barbell-hip-thrust/ ; https://www.nasm.org/resource-center/exercise-library/barbell-bench-press ; https://www.nasm.org/resource-center/exercise-library/seated-machine-row-close-grip
- 橙色是肌群位置示意，不是肌电/激活百分比；样片未经教练专业审核。
- 人物采用原创分段式关节人偶，肌群标记使用贴合表面的简化区域；文件支持继续编辑，尚未执行专业动作审核。
- 输出来源、肌群参考和重新生成命令记录于 docs/animation-samples/README.md；数值验证在 validation.json。

## 希腊雕塑资产管线
- 复用 Whimphony 官方 tripo-cli@0.5.2 / v3 image-to-model → rig-check → Mixamo rig 流程；使用既有本地授权 profile，未复制任何凭证。
- 男女设计三视图及 imagegen 单人物正面输入保存在项目中。高清几何/PBR 各消耗 60 credits；male 48,498 / female 49,278 三角面。
- 两套模型免费 rig-check 均返回 riggable=true, rig_type=biped；已检查 Blender 中正背面，继续绑定标准人体骨架。
- 单正面输入会重建背面而非逐像素匹配三视图；女性背发简化，后续可在 Blender 雕刻细化。

- Mixamo rig 两套实际返回 23 节点；male 27,438 顶点，female 27,816 顶点；无权重顶点均为 0。
- 女性胸部修整需按空间位置合并 UV 接缝的邻接关系再平滑，直接 Smooth modifier 会把断开的 UV 顶点拉开。最终实现保持原索引，局部修改 1,284 顶点并重算区域平滑法线。

## 肌群表面示意参考
- OpenStax A&P 2e 11.5: 胸大肌为前上胸扇形，背阔肌位于背部中下段，三角肌包覆肩部。https://openstax.org/books/anatomy-and-physiology-2e/pages/11-5-muscles-of-the-pectoral-girdle-and-upper-limbs
- OpenStax A&P 2e 11.6: 前大腿股四头肌、后大腿腘绳肌、臀大肌、腓肠肌等位置。https://openstax.org/books/anatomy-and-physiology-2e/pages/11-6-appendicular-muscles-of-the-pelvic-girdle-and-lower-limbs
- 设计采用体表区域叠加，与现有网格同一蒙皮；不是独立的解剖实体肌肉，不能表达深层组织层次或收缩体积。女性胸部区域为胸大肌位置投影，不能把乳房当作肌肉。

- 肌群区域采用人体表面近似分区，纤维映射按群定向；不是解剖剥离、深层肌肉或物理收缩模拟。衣物处仍保留衣褶几何。
- 原始 Mixamo 上臂骨轴偏离体积中心，导致男右肱二头区域漏选；使用实际 Arm 蒙皮顶点的前后 5/95 分位中心校正区域坐标，未修改骨架。
- 初始小腿门限过窄，导致腓肠肌中部断带；扩大表面候选半径后已修复。
- ID atlas 为 Non-Color 0–17，17 个独立灰度 mask 互不跨 ID；实际 GLB 有 18 个材质分段，移动端可改用单材质 ID shader。

## 动作样片 v2
- 延续深蹲、杠铃卧推、窄握坐姿绳索划船，替换为已选男女雕塑与肌群材质；采用现有器械几何设计。
- 参考 NASM 卧推、划船和 ACE 动作知识；仅用于姿态检查，不读取或提取上游 GIF 动作数据。https://www.nasm.org/resource-center/exercise-library/barbell-bench-press ; https://www.nasm.org/resource-center/exercise-library/seated-machine-row-close-grip ; https://www.acefitness.org/resources/everyone/exercise-library/

- v2 首轮检查：自动蒙皮把部分脚面归于小腿，脚踝校准后仍有脚底漂浮；在动画副本中重新分配足/手远端权重。卧推顶点和划船脚位首次略超两骨长度，按实际男女臂长和腿长收回目标点。

- v2 媒体全帧边界检查发现卧推平台底缘裁切（动作与人物未超出范围）；扩大正交相机尺度并降低取景中心，只重新渲染卧推男女版本。

- v2 最终 720 帧无边缘裁切；6 个原生动作场景的脚底表面关键帧漂移 <0.1mm。该数字是渲染蒙皮的数值稳定性，不表示真实人体动作精度。
- 姿态及肌群仍是视觉制作样片：手部采用统一握持修形，无逐指骨骼；深屈伸会出现自动蒙皮体积损失，斜方肌使用现有表面区域贴图。

## 2026-10-28：手指骨骼和握持问题
- 用户指出 v2 卧推手部未握住杠铃。旧实现只有整体 `Grip_Corrective` 形态键，且握点是经验偏移；原始 Mixamo 骨架仅有 Hand，没有逐指骨骼。
- 在旧男性卧推实际蒙皮上测量杆轴周围的近接触区域，只覆盖 12 个角度扇区中的 8 个；部分手部顶点深入 14 mm 半径的杆内。旧目标点误差检查不能发现该问题。
- 原始男女模型具备可辨识的五指几何。动画副本焊接导入重合顶点（保留面角 UV），为每手 5 指各增加 3 根 FK 骨骼，分配归一化的手指/掌心蒙皮；总骨骼数 23 → 53。
- 根据手部局部 X 轴设置杆轴朝向，使用实际掌心位置求腕部 IK；四指绕杆闭握，拇指从另一侧对握。划船为竖向中立握；调整伸臂目标 25 mm 使新腕部偏移仍在可达范围内。
- 用实际混合蒙皮矩阵的逆变换生成左右手接触修形，适配直径 28 mm 的杆。手指弯曲由骨骼产生；接触形态键只处理穿杆。其他杆径和手势应重校正。
- 深蹲的手与杆随躯干同步绕杆轴转动；在器械局部坐标中检查滑移，避免将绕轴旋转误判为脱手。
- 新检查在 60 个手部关键姿势验证至少 10/12 个近接触扇区、每指靠近杆面、无深度顶点穿杆、相对器械无滑移；额外旋转食指根骨确认网格真正变形。
- 新独立资产位于 `docs/character-assets/hand-rig-v1/`，保留肌群开关的 Blender 源文件和白色雕塑材质的 GLB，含单段张手/闭握动作。GLB 重新导入后确认 53 个 joints、30 根有权重的指骨、形变与闭环正常。
- 原人物/肌群源资产不覆盖。低模手指在极近镜头仍有棱角，当前为 FK 手部，不含逐指 IK 或自动碰撞求解。

## 2026-10-28：深蹲杠铃穿肩与颈后异常隆起
- 独立肩背近景和 BVH 检查复现旧深蹲的穿模；手部握持与四肢长度通过，不能证明躯干与器械接触正确。
- 原始男性雕塑后侧上背体积偏厚；放松手臂的对照仍可见隆起。上背还混入上臂权重，抬臂时产生约 35 mm 的局部拖拽。
- 根据接近伸直的源肘部平面推导上臂扭转不稳定，深蹲中造成肩部扭曲。改用躯干局部的最小摆动旋转，保留手腕与五指接触姿势。
- 新增 `shoulder_rig.py`：在人物副本平滑收整后侧上背、将中央肩颈不合适的上臂权重转回躯干。男女的形体调整幅度分别设定，原始源资产保留。
- 杠铃改为基于实际上背表面的 28 mm 杠轴相切位置，按人物尺寸分别求解；站立髋部高度和躯干倾角同步调整，杠轴保持在足中部附近。手臂和杠铃跟随同一躯干坐标系，避免相对滑移。
- 最近面法线在肩部凹陷外侧会误判“在体内”，独立验证改用三方向射线奇偶性确认深度穿模，并检查双侧接触间隙。全循环男女各 121 帧（242 个姿势）通过。
- 新增正/背/侧面检查图和旧/新对照。侧面近景隐藏配重以看清杠轴关系；正式动画保留完整器材。
- 文字位置参考：NASM 的 Squats and Deadlifts PDF 中 high-bar upper trapezius 描述；没有复制第三方影像或动作数据。

## 2026-10-28：可复用动画流水线
- 当前三种运动已具备共用的人物/蒙皮校正、有限并发渲染、模型导出、打包与验证步骤，可统一编排。
- 新增动作仍需实现运动轨迹、器械、接触坐标系和对应检查；元数据注册不是自动动作生成。验证脚本仍有明确的动作枚举，扩展时需一起更新。
- 增加 `exercise_catalog.py` 集中标题、数据集 ID、阶段与主要肌群；`pipeline.py` 提供 full / verify / dry-run，依赖预检、阶段失败停止及每次运行日志。
- 新增流水线文档说明了中间帧不入库、新 checkout 需要 full、当前字体/工具依赖、目视审核，以及未来可提取的动作/器械/接触接口。
- 对 15 个新增 Python 脚本统一格式化，逐个比较格式化前后 AST，确认格式整理不改变语义。

## 计划动画扩展 · 需求盘点
- 用户指定 workout_plans/recomposition-4day-2026-10-28-v3.json：四周共 19 个唯一正式动作，卧推 0025、划船 0861 已有，缺少 17 个动作（需 34 段男女视频）。现有深蹲不在该计划内，继续保留。
- 计划备注的周五弯举/三头与正式动作重合；有氧、热身、活动度只在 notes 中，没有正式 exerciseID，不能伪造映射。
- 当前生成器只实现 squat/bench/row；不能把新目录项目直接加进来跑，否则会误入划船分支。
- 原指骨、肩颈修正、肌群材质、原生 Blender 工作流和 App 媒体清单可复用。坐姿腿弯举的上游中文步骤存在方向表述问题，以具体器械运动/解剖参考核对。
- 动作参考（只参考文字与运动规律，不复制视频）：NASM seated-leg-curl、dead-bug、romanian-deadlift-barbell、two-arm-incline-dumbbell-chest-press。坐姿腿弯举应向下屈膝；死虫式为对侧手脚交替；RDL以髋铰链为主；上斜卧推采用靠背与稳定落足。
- 采用独立 plan_exercises / plan_motions 扩展适配器和 animation-plan-v3 输出，保留旧三动作流水线默认行为；复用角色准备、IK/FK、肌群、渲染与握持清理。新批处理支持预览与断点续作。

### Plan animation key-pose review
- All 17 new motions bake with stable limb lengths and closed loops for both characters after reducing pulldown reach to fit calibrated arm length.
- 30 closed-hand scenes passed mesh-surface grip checks (five sampled frames, digit proximity, radial coverage, drift and actual finger deformation).
- Visual review of both sexes identified RDL bar behind thighs, pulldown back support obscuring the muscles, and missing leg-machine handles. Corrected these before final rendering; rigid two-hand bars now use shared world targets, not independent left/right FK endpoints.
- Core motions use open hands; reverse crunch lifts the pelvis ~6 cm with upper torso fixed; dead bug alternates opposite arm and leg over an 8-second loop.

### Final animation checks / 2026-10-29
- Pixel-alpha checks exposed cropped stage edges in 20 clips and a clipped tower top in straight-arm pulldown. Added automatic orthographic fitting from evaluated mesh surfaces over 17 poses, with 3.5% margins, and re-rendered the affected scenes.
- Supine male scapular volume initially penetrated the mat. Adjusted support height and added an explicit post-skin underside contact modifier; source character remains unchanged. Final mesh minima: supine 0.028 m (mat), calf raise 0.100 m (step).
- Final resource validation passes: 19 formal plan IDs, 34 new videos, 4,224 rendered frames, H.264 full decodes, no edge clipping, SHA-256 correspondence to all bundled media. App keeps original squat too: 20 motions / 40 videos and posters, about 16 MiB.
- Preview filtering and character switching verified in IAB. Native fullscreen request was unavailable in this host, so the review page uses a viewport-filling dialog with an explicit close control; video object-fit is contain.
- Full UI suite exposed an existing fixture assumption: animation test required an empty plan after another test had imported/completed a sample workout. The animation test now reuses the known sample plan when present and opens its next workout demo, without clearing state. Re-running all four UI tests.
- Final full UI suite and runner succeeded after handling both the existing sample plan and its in-progress draft. Final built App contains 20 motions / 40 valid media variants; 14 missing Chinese labels are generated from motion metadata.

### Collision repro (red), 2026-10-29
- Command: `blender -b --python-exit-code 1 --python Scripts/animation_samples/collision_audit.py -- --exercise leg_press --sex male --frames 61 --output build/collision-repro.json`.
- Actual evaluated-body vertices inside closed equipment volumes, >2 mm, nearest-distance plus three-ray parity confirmation. Fails: Back support 49.98 mm / 2090 vertices; Sled footplate 34.73 mm / 420; Back frame 33.13 mm; seat-handle connectors ~17 mm into fingers.
- Ranked hypotheses communicated before fixes: (1) equipment placement references bones rather than skin, (2) connectors invade the gripped segment, (3) extreme poses cause body self-intersections. Full 38-scene baseline underway, before modifying source motion/equipment.

### Collision baseline and fixes / 2026-10-29
- Baseline audited all 38 plan scenes. Original leg-press repro deterministically failed with 50 mm back-pad, 35 mm footplate and 17 mm handle-connector penetrations.
- Added bidirectional evaluated-mesh containment (including subdivided equipment edges for thin rods) and nonlocal body-surface intersection checks. Strict penetration tolerance remains 2 mm. Same anatomical patch/local connected joint seams are not treated as separate solids; no object-wide equipment exemptions.
- Found source hand triangles spanning the bar cavity despite vertex-radius checks passing. Local hand subdivision before the inverse-skin grip corrective removes these surface crossings; original 53-bone rig and UVs remain.
- Support pads now fit evaluated skin over the complete cycle; connectors attach outside palms. Leg-press soles now face the sled, and shin rollers fit actual shin surfaces. Remaining checks include body folds at knees/hips/elbows and end-range movement conflicts.
- Five independent geometry fixtures pass: interior vs exterior, contact tolerance, long thin rod with outside endpoints, nonlocal body crossing, and shared topology.
- Whole-cycle auditing caught failures absent from 9 key poses: male pushdown index-finger surface at frames 3/119 and female shoulder folds in fly/dead-bug transitions. These are repaired in geometry, without changing the 2 mm gate.
- Leg press now uses a 1.0-radian reclined backrest with relocated handles, opening the hip angle; avoids excessive pelvis smoothing. Hip relaxation reduced to 50 iterations, knee to 100. Closed grip subdivision preserves skin thickness instead of relying only on vertex radius.
- Motion views reviewed for all 38 scenes: front, side and back at both endpoints, plus both dead-bug sides. Diagnostic images are in build/collision-review; small joint folds/individual finger contacts remain a visual review concern outside nonlocal-collision scope.

### 形变调研纠正 / 2026-10-29
- 详见 docs/research/character-deformation-audit.md 与 primary-sources.md。
- RDL 男性第61帧关闭普通 Smooth 后肘周平均变化15.7mm、最大36.2mm，细缩减轻但扭曲仍存；卷腹脚部变化为0。DQ不能独立解决两者。
- 当前两场景权重总和近1、骨骼变换无非预期缩放，不能因此断言权重分配/骨骼朝向正确。后续分离姿势、绑定、蒙皮与后处理。

### Binding repair evidence
- 统一前臂运输坐标后，旧硬拉肘部的约128/143度额外roll消除。加入每前臂两根辅助扭转骨（总57骨），把腕部旋转分布到前臂，避免在肘缝集中扭转。
- 脚部过渡改为实际踝中心上下各2.5cm模型空间，脚趾分配独立权重。校验实际deform权重归一化，不包含材质/修改器遮罩组。
- 加强普通Smooth被移除。试验有rest参考的Corrective Smooth 5–60次仍未解决剩余卷腹关节交叠，因此未加入生产绑定。
- 卷腹原屈肘约130度；将握点稍向前，髋部略在膝前（保持小腿贴垫）后，两性关键帧的交叠消除。动作仍由脊柱逐段屈曲，非用伸缩肢体达标。
- 共享绑定抽取到 prepare_athlete.py；原雕塑未修改，候选文件在 build/rig-repair/candidate，未覆盖已交付视频。

### 握持修正的第二个形变根因
男性下压的全循环检查暴露旧圆柱硬投影把内外皮肤层压到同一半径，射线在约 10–30 微米内反复穿过薄片。该动作改用严格递增的径向位移并向外衰减，保留手指壁厚。新模式左右 Shape Key 均从 Basis 创建：Blender 默认 from_mix 会把已激活的左手修正复制进右手 key，造成左手叠加两次；手部接触间隙检查及时发现并阻止输出。旧投影模式保留现有已验收场景配方兼容性，新模式禁止这种混合复制。

## 卷腹握绳方向修复（2026-10-29，补充）

此前的形变与接触检查漏掉了“位置正确但握持方向错误”。旧卷腹在第 61 帧有男性 163.28°、女性 165.77° 的手腕/前臂补偿扭转；表面包覆和碰撞仍能通过，因此不能只凭那些指标验收。

修复 `plan_motions.py` 中卷腹的握把坐标：两掌相对、食指/拇指端朝向上方绳索；对可倾斜的绳索握把迭代求解手腕与前臂轴线，同时保留固定拳心目标和骨长。不是限制扭转数值来掩盖错误姿态。只改此动作，男女均重新烘焙。

新增 `verify_grip_orientation.py`：每个版本逐帧检查手腕轴转、手腕折角、两掌相对和食指端朝上。用食指/小指根部连线确定拳头的拇指端，不能把靠近手腕的拇指根误当作拳头顶端。当前运动专用阈值为轴转 ≤90°、折角 ≤15°、指端向上点积 ≥0.25、手掌向内点积 ≥0.5，不是人体通用活动范围。最终男性/女性全循环最大轴转分别 27.52°/31.63°，最大手腕折角 <0.03°。旧场景在同一检测器下失败，首次仅修改坐标的试版也因约 60° 折腕失败。

两个场景各 121 帧通过方向、形变、碰撞检查；另有五帧表面包覆/每指接触/循环检查及正侧背、器械可见的手部近景人工查看。`grip-orientation-validation.json` 与场景、检测器哈希绑定，并接入渲染、打包、App 同步的形变门禁。其余动作尚未拥有此类动作专用握姿方向约束。

## 2026-10-29 死虫式肩腋问题：仍未修复
男女均已复现。垫面不是主因；权重、锁骨、蒙皮及姿态修正试验尚未获得可交付结果。撤回两项视觉验收，现有视频保留，生产门禁拒绝该动作。具体证据和未完成事项见 `docs/animation-plan-v3/known-issues/dead-bug-axilla/README.md`。不要在后续汇总中把前一轮的“19 动作通过”沿用为当前全部合格。

## 全库制作盘点（2026-10-29）
- 当前 App 文本目录 1,324 个唯一动作，28 种器械；现有原创媒体目录 20 个动作、40 段视频。缺少 1,304 个动作的男女实现。
- 现有 19 动作新门禁中，死虫式男女视觉审核被撤回；深蹲属于旧版流程，不能声称它已通过新门禁。
- `plan_pipeline.py`、运动求解及校验当前显式枚举 19 项；新增元数据不会生成新动作，不能对全库直接运行并声称覆盖。
- 完整库包括力量、拉伸、平衡、有氧与多种未建模器械，需要动作专用轨迹和接触规格。盘点以精确 ID 关联成品，不按名称模糊复用。
- 本机剩余磁盘约 146 GiB；当前 19 动作源场景约 1 GiB，原始帧及历次候选占用 build 约 11 GiB。全库必须分批处理原始帧，不能无上限并发渲染。
- 用户确认完整范围、男女版本、分批交付。首批精确 ID：0285 交替哑铃弯举、0310 前平举、0313 锤式弯举、1678 坐姿锤式弯举。
- 0313 上游步骤误写“旋转掌心朝前”，与名称锤式弯举不符；制作按 Rogue 官方中立握示范（https://www.roguefitness.com/theindex/movement-library/movement-demo-hammer-curls），不复制其图片或视频。前平举参考 ACE（https://www.acefitness.org/resources/everyone/exercise-library/54/front-raise/）：正握、抬到肩高、保持腕中立。
- 首轮男性锤式弯举关键帧复现：哑铃片侵入大腿约 48 mm；原模板以世界竖轴设握持，实际腕骨有约 25° 折角。新适配器按真实腕骨方向对齐前臂，并调校臂侧间距；保留原门禁和 2 mm 碰撞容差。


## 死虫式肩腋修正结果（2026-10-29，替代此前未修复状态）
当前可交付方案是 DQ 蒙皮之上的局部姿态 Shape Keys：带上臂/躯干体积约束的保形表面求解，逆蒙皮回形态，再检查插值后的实际皮肤接触。女性衣褶需要独立保护，不能套用男性裸露肩部的全部表面修正。原网格/UV、全部骨轨迹保持不变；不是通用蒙皮算法替换，也不是原权重问题已全部消除。

男女完整 193 帧拉伸 p95 最大值分别 1.79515 / 1.79699，原 1.8 回归阈值、2 mm 碰撞容差不变。两版全帧形变/穿模、闭环与多视角/近景审核通过后已替换成品，局部雕塑折痕仍可见。增加逐帧拉伸报告和肩腋近景门禁，避免仅看整体轮廓漏验。该配方仅覆盖当前两个角色的死虫式；推广到新动作仍需重新校准和审核。

## 第 002 批动作语义
- 0335 原库步骤明确为侧举→下放→前举→下放，不做肩高水平转臂。0387 掌心向身体采用中立握；0392 掌心向下采用正握。
- Full can 参考 OrthoVirginia 机构原始肩部练习图，采用侧向前约 30° 肩胛平面、拇指向上至肩高：https://www.orthovirginia.com/wp-content/uploads/2022/04/IMPINGEMENT-SYNDROME.pdf 。反握弯举对照 PureGym 自有示范，掌心向下保持前臂旋前：https://www.puregym.com/exercises/arms-and-shoulders/bicep-curl/pronated-bicep-curls/ 。只参考动作语义，不使用其媒体。
- 男性反握弯举的零星握杆/拇指接触来自原 thumb 闭合轨迹：末端骨目标半径约 11 mm，小于 14 mm 握杆，靠表面投影会压扁局部皮层。独立保厚候选改坏食指，17 mm 净空只把问题转移至右拇指；现保持原全局净空和检测器，针对该动作男女中有问题的男性增大拇指末两节的径向路径。其余角色/动作默认参数不变。

## 第 003 批规格
- 0404 名称为 parallel grip，但上游第二步误写手掌朝前；制作与文本明确保持掌心相对。上斜锤式凳角 45°，3545 左右交替；平凳 0352 中立握需比 0289 收肘。参考 NASM 自有上斜推举说明 https://www.nasm.org/resource-center/exercise-library/two-arm-incline-dumbbell-chest-press 和 Baylor 原始教材 https://www.baylor.edu/content/services/document.php/86940.pdf ，只参考语义，不复制媒体。
- Baylor 原教材链接本次返回 404，未读取全文；实际制作核对采用已读取的 NASM 原文（45° 凳角、受控推起和下放、腕肘对齐），Baylor 搜索摘要不作为完整来源证明。

- 第 003 批平卧支撑反例：统一躯干旋转会保留原站姿后脑/上背与臀部不同的深度，最低点贴凳并不等于三点均受支撑。女性增加约 4.9° 躯干摆放，男性单独回调颈部；上背与头部分区独立测量，旧版本保留作为拒绝证据。

## 第 004 批动作规格（2026-10-30）
- 精确 ID：0315 上斜哑铃弯举、0320 上斜锤式弯举、0298 跨体锤式弯举、0439 佐特曼弯举、0414 站姿交替推举、0415 站姿交替侧平举、0406 哑铃耸肩、0293 俯身哑铃划船。保持男女版本，上游 submodule 与媒体不修改。
- 全部核对 pinned 上游文字指令。辅助一手示范文字：Catalyst Athletics 上斜弯举（https://www.catalystathletics.com/exercise/850/Incline-Dumbbell-Curl/）明确靠背与上臂垂直悬垂；M&S 自制跨体教程（https://www.muscleandstrength.com/exercises/hammer-curl-across-the-body.html）明确交替朝对侧胸部且哑铃不接触躯干；M&S 佐特曼教程（https://www.muscleandstrength.com/exercises/zottman-curl.html）明确掌心向上举起、顶部旋前、反握慢放；ACE 站姿耸肩（https://www.acefitness.org/resources/everyone/exercise-library/75/standing-shrug/）明确直臂向上提肩，不绕肩。仅取动作约束，不下载其媒体。
- 采用独立 v4 检查模块和规格摘要绑定，保留已交付 v1/v3 检查源码及凭据。0315/0320 倾角相同而握姿不同；0415 必须侧举而非前举；0406 必须抬肩而非屈肘；0293 保持俯身躯干与双脚固定。

## 2026-10-30 蝴蝶机参考与机构约束

旧蝴蝶机把器械简化成门框和随手部伸缩的斜杆，不能表达真实机构。参考 Life Fitness Insignia Pectoral Fly / Rear Deltoid（SS-FLY）官方照片，改为固定竖直转轴上的定长摆臂，以圆周轨迹约束握把，人体反向求解跟随器械。男女采用各自静态尺寸，动画中连杆长度不变。新增全循环机构验证，照片来源及验证脚本 SHA 与场景验收绑定；人工验收必须含主视角与侧视角器械证据。模型为原创简化结构，不是制造商精确尺寸复刻。参考记录见 docs/equipment-references/pec-deck.json；此后建模先实际查看产品照片的要求已写入 AGENTS.md。

- 第 004 批最终几何修正：上斜弯举背垫宽 28 cm，横向握柄弯举在中段为大腿留出净空；女性划船增大少量手臂外侧净空；跨体弯举独立解算胸前路径，女性采用较低的收缩顶点以避免肘窝表面自交。最终 16 版共 2,512 帧全部通过，2 mm 碰撞标准未变。
- 佐特曼采用 M&S 教程的掌心朝前起始版本；在 prepare_resources.py 中显式覆盖 0439 文字步骤，使 App 的起始握姿、顶部旋前与底部复位和成片一致，保持上游 submodule 不变。
- 已实际查看 16 张五视角审核表（佐特曼各含 8 个帧位，含 73/85/97 和 169/181 的转腕过程），逐项写入 scene/evidence SHA 匹配的验收决定。8 个错误场景被拒绝（6 个规格错配、2 个旧扭转跳变），8 个正确规格对照通过。

## 2026-10-30 全器械照片复核
实际打开并查看 Life Fitness 官方 2025 产品目录 PDF 的第 34、37、39、44、48、75 页照片。结构观察、型号和来源记录于 docs/equipment-references/equipment-audit.json。当前需要补齐绳索回程/升降配重、腿机膝轴支架/传动、腿举挂片/导轨承力、提踵肩垫承力架、训练凳靠背支撑。自由重量本体结构与照片相符，保留简化造型。

## 第 005 批选型与器械参考
已查看官方 2025 目录第 39、44 页实物照片，记录于 equipment-references/batch-005.json。选择八个独立单臂 ID；1669 的上游要求肘靠大腿，不套用普通坐姿弯举，留待后续专门制作。1671 名称为单臂而上游步骤误写双臂，需按单臂原始教学来源修正应用步骤。

1671 已核对 M&S 单臂锤式弯举教学；1281 参照 NASM 单臂上斜推举的 45° 靠背、躯干抗旋转和一次完成一侧规范。新 v5 检查器绑定本批器械照片记录摘要，旧版验证器保持不变。

用户要求核对最新制作流程：2026-10-30 逐项读取 AGENTS.md、animation-pipeline.md 和器械照片流程。发现新握持优先试用保留指厚遗漏，已终止旧候选队列，改用 preserve_thickness 并关闭空闲手的器械接触形态键；全批重新烘焙、检查和生成审核证据。旧 App 成品未变。

保留指厚关键帧检测定位男性食指根部三角面的弦切穿握柄：顶点半径约 16 mm，但跨弧面片的最近点半径只有约 11 mm。新增局部按握柄轴夹角细分，保留面片/UV/权重且不扩大修形间隙或碰撞容差；应用于本批保留指厚配方。

第 005 批最终验证：v5 场景默认保留指厚，空闲手关闭接触修形；细化粗面片后保持原 2 mm 碰撞阈值。新增独立单臂检查约束负重侧、空闲臂、固定躯干和刚性器械；平凳及上斜凳须有主/侧三姿势照片对照证据。最终 16 版完整检查和人工审核通过，8 个真实错误场景被拒绝、8 个正常场景通过，38 项门禁/交付/并发测试通过。新旧资产均已同步验证，全部 1,324 项的制作仍待后续批次推进。

## 肢体修复诊断
现有男性源模型小腿已有鼓圆和膝下过渡生硬；动画站姿更明显，不能仅以穿模通过放行。候选原因依次为原造型、腿骨轴转/站姿、局部权重，逐项隔离。参考 OpenStax 下肢肌群章节（https://openstax.org/books/anatomy-and-physiology/pages/11-6-appendicular-muscles-of-the-pelvic-girdle-and-lower-limbs），不复制其媒体。

肩腋关键对照：旧 DQ 结果抬臂时侧胸弧形外鼓；全区域体积求解会引入尖折且接触投影超过限额。局部肩带 DQ→线性目标的逆蒙皮修形在男女推举关键姿势明显改善，已通过九关键帧碰撞/形变/动作检查，正在全帧复核。保持 Armature 的 DQ 设置，肘腕、手指及纯上臂区域不全局切换算法。

### 2026-10-30 肢体修复的动作适用边界
- 新站姿用于静立类动作；RDL 原轨迹含髋部前后位移，直接使用更高静立髋位会超过腿链长度。保留硬拉原有独立屈膝余量，IK 检查不变。
- 女性平卧推举的 DQ→线性肩带试验在胸前伸臂阶段出现约 2–4 mm 的上臂/躯干相交；中立握卧推另有凳面逆向穿入。原平卧肩部配方的现有五视角图没有推举中的大侧胸鼓包，因此平卧四种动作保留原肩部蒙皮，只更新下肢轮廓，重新烘焙并按原标准验收。不能把站姿推举配方盲目覆盖全部动作。
- 本轮已重新实际查看留存的官方目录照片第 34、37、39、44、45、48、75 页，用于接触重新拟合后的器械支撑比对；不改变既有承力机构。

## 第 006 批规格初选
0333/0354 为站姿双臂/单臂俯身臂屈伸，0394/0398 为坐姿双臂/单臂；2317 固定 90° 屈肘侧举；0419 前举至头顶；0437/0363 为双臂/单臂肘带动直立划船。逐条读取 pinned 数据文字；本批新增独立轨迹与 v6 检查，不以重命名已有视频交付。

已实际查看官方目录第 39/44 页照片：平凳长垫、纵梁、前后支腿和横向底脚，哑铃中央柄/对称负重。新坐姿凳按此结构实现。ACE 原创 kickback 教学核对上臂固定、肘约 90° 到伸直和躯干不旋转（https://www.acefitness.org/resources/everyone/exercise-library/55/triceps-kickback/）；具体站距与坐姿由 pinned 动作规格确定，未复制教学媒体。

实际查看坐姿双臂臂屈伸男性五视角诊断图：凳体支撑正确、躯干与上臂稳定；回收时手位与大腿重叠。调整前臂屈伸平面，保持 90°→8° 肘角和固定上臂，不靠扩大皮肤间隙/容差放行。二轮关键帧 11/16 通过；过顶肩腋、直立划船肘窝及坐姿前倾躯干/腿部重叠已消除。

第 006 批最终：通过调整屈伸平面、坐姿开膝、空闲手位置、肩带上旋和划船前臂方向，16 个版本全帧检查及实际画面审核通过，2 mm 容差保持不变。通用握持机位在臂屈伸末端可能被躯干遮挡，因此新增每只负重手三个阶段的外侧独立近景，v6 门禁要求记录对应图片摘要。坐姿要求完整凳体主/侧视图。最终 7 类真实错误场景均被拒绝，全部交付与原有资源不变证明见 batch-006.json。

用户截图表明单臂动作的负重左手被躯干遮挡。现有 11 个单臂动作均为 Left，主镜头沿用正 X 侧，实际面向空闲右手。将主镜头转到负重侧，并保留人体、动作和器械的几何不变证明；不能仅靠正背面或手部补拍替代主画面的可见性。

单臂上斜推举还属于 equipment_refit_catalog.MOTIONS，除了 v5 检查外必须重新生成独立器械机制及照片对比记录。相机修改也会改变场景摘要，因此旧记录不能直接搬到候选；当前补跑完整器械检查并将只更新这两个记录，其他器械验收保持。

最终负重侧主镜头修正覆盖全部 11 个现有单臂动作、22 个男女版本。完整循环几何相等证明显示人体、器械和轨迹未变；主镜头原先正 X 朝空闲右手，改为负重左手近侧后，臂屈伸的肩肘腕与哑铃路径不再藏在躯干后。实际逐项审查后放行；肩深度只作为自动机位判据，不取代主画面可见性审核。

## 2026-10-30：真人动作参考缺口

用户指出双哑铃直立划船肩肘失真。现有无碰撞/骨长/形变通过不证明动作合理；动作必须有匹配变体的真人参考。第一方来源、版权条件和动捕限制见 `docs/exercise-motion-source-research.md`，制作规范见 `docs/motion-references/README.md`。已实际查看 NCSF PDF 第 6 页的真人错误/修正对照；不能把肘高过肩一概认定为人体不可能。MM-Fit 指定视频版本官方元数据为 CC BY 4.0；Fit3D/FLAG3D 默认非商业；Gym visual 常规条款限制作为 AI 生成素材基础。没有验证到覆盖全部 1,324 项且满足生产用途的单一来源。

## 直立划船缺陷根因与防回归

旧场景真实审核样本显示上臂峰值135.81°，原动作检查只要求肘高于腕、腕接近肩和一定屈肘量，没有抬臂上限。降低到83.83°后，第一候选因前臂过靠内导致哑铃入躯干；保留真实握持并增加前向路径后，4个完整循环无碰撞或形变失败。未改公共绑定和器械。新检查选定的是本示范动作范围，不宣称人体关节绝不可能超越90°。

motion_reference_gate.py要求实际真人四阶段观察记录与动作规格匹配；全帧报告绑定场景、参考和检查器，视觉意见绑定对应来源时间点和当前渲染证据。历史兼容仅限固定scene/spec摘要，重新烘焙没有豁免。新规范未自动补齐其他所有旧动作参考。

## Git 历史清理边界（2026-10-30）
当前 main 有 5 个提交，origin/main 的本地记录仍指向含旧媒体的 2d09575。另有 Codex 内部 tree 引用及 reflog，不能只清理主分支。工作区存在其他任务未提交结果，必须保持索引和文件不变。系统没有 git-filter-repo，将在私有工具目录安装并只用于隔离副本。

### 第007批参考核对
- 1669：OPEX Fitness 真人单手坐姿锤式弯举，0.000 / 0.600 / 1.251 / 1.851 秒；右手示范，项目左手独立求解并采用近侧机位。空闲手、躯干及坐凳稳定。
- 1739：Functional Fitness 真人交替臂屈伸，4.144 / 4.744 / 5.344 / 6.216 秒；8.288 秒另侧伸肘。ACE 第3页补充上臂固定及躯干不扭转原则，其支撑站姿不能替代交替变体参考。
- 本批增加 v7 检查，保留 v6 等历史检查器摘要；交替动作的四阶段对照应为单侧完整重复（1/25/49/73帧），不能误用全片四等分导致把换侧低位当峰值。

历史清理验证：仅清 main 不足以排除 refs/codex 下 tree 快照的资产；这些引用也要盘点。采用隔离 bare 改写和原子 update-ref，避免 dirty 工作目录被 reset。推送 hook 必须扫描完整祖先，并结合已移除 blob ID 阻止改名重入；安装副本放在 .git，避免切换旧提交使 hook 消失。并发工作期间保留不可达对象缓存，不执行 prune=now。

## 第 007 批交付完成（2026-10-30）

按真人参考优先流程完成 1669 坐姿单臂锤式弯举、1739 站姿交替哑铃臂屈伸，男女双版本。OPEX / Functional Fitness 真人阶段观察和器械照片核对在制作前完成；单臂动作使用近镜头负重手，交替动作分别验证左右完整重复。初始空闲臂外展、上臂外张和女版低位器械碰腿均在交付前修正，保留拒绝记录并增加回归检查。

628 帧完整循环检查、624 帧正式渲染；逐项目视五视角、握持近景及最终编码采样，通过 27 项单元测试、8 个真实场景错误对照和 2 个阶段映射错误对照。四段正式视频经浏览器完整播放，5/8 秒、1280×960、无媒体错误；第 007 批默认展示和女性版本切换正确。交替动作远侧上臂在主镜头部分遮挡，已用侧/背视角核验，不声称所有关节在主镜头均无遮挡。

预览与 App 已同步，Xcode 模拟器构建成功，265 个构建资源摘要一致；旧 64 项目录、256 个媒体及 88 个库场景保持原样。现累计 66 项 / 132 段视频，1,258 项未制作。详见 docs/animation-library/batch-007.json。
