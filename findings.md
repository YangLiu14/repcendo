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
