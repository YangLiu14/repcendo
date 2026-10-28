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
