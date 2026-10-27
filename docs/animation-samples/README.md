# 渐强：原创动作样片 v01

2026-10-27。三个 5 秒循环动画，用于评估人物风格、动作表达和肌群标记方式。
打开 `index.html` 查看；点击「同时播放」，或在每段视频中单独播放、暂停、拖动。
本次交付独立样片，尚未接入 iOS App。

| 样片 | 关联动作 ID | 橙色标记 | 文件 |
| --- | --- | --- | --- |
| 杠铃深蹲 | 0043 | 股四头肌、臀大肌 | squat.mp4 / squat.gif / squat.blend |
| 杠铃卧推 | 0025 | 胸大肌 | bench.mp4 / bench.gif / bench.blend |
| 窄握坐姿绳索划船 | 0861 | 背阔肌、肩胛间区域（菱形肌与中斜方肌） | row.mp4 / row.gif / row.blend |

## 如何理解肌群标记

橙色表示主要训练肌群的大致体表位置，不代表肌电、激活百分比或各肌群的贡献比例。
右侧的正面、背面图补足动作镜头的遮挡。肩胛间标记是区域示意，未尝试在体表显示菱形肌与斜方肌的真实解剖分层。
没有标橙色的肌肉仍可能参与动作，例如卧推中的肱三头肌、三角肌前束。

人物是分段式关节人偶，采用简化的体表区域，不是精细解剖人体。
这些样片尚未经过教练或运动专业人士审核，当前用于视觉与制作流程评估。

## 原创来源与编辑

人物、器械、肌群区域、运动轨迹全部由本项目的 Blender Python 脚本生成。
没有导入或描摹 Gym visual 的 GIF、图片，没有使用其提取的姿态数据；也没有导入第三方模型、纹理或动作库。
文字使用本机字体渲染，未分发字体文件。

- Blender 5.2.1 LTS；Workbench 渲染；命名关节节点与逐帧变换关键帧。
- `.blend` 保留完整几何、材质、相机和 121 帧关键帧；渲染范围为 1–120 帧，121 帧用于验证闭环。
- 第 1 帧为起始姿势，第 61 帧为最低点或拉回位置。
- 人物不是蒙皮绑定模型。若后续需要更自然的连续皮肤，可以保留轨迹并更换模型和绑定。
- MP4：1280×960、24 fps、120 帧、H.264；GIF：960×720、16 fps、无限循环。

## 重新制作

在项目根目录执行。需要 Blender 在 PATH 中，以及 Python 的 Pillow 和 ffmpeg。

```sh
python3 Scripts/animation_samples/render_samples.py
python3 Scripts/animation_samples/package_samples.py
python3 Scripts/animation_samples/verify_samples.py
```

只生成关键姿势预览：

```sh
python3 Scripts/animation_samples/render_samples.py --previews-only
python3 Scripts/animation_samples/package_samples.py --preview
```

中间帧及日志保存在已忽略的 `build/animation-samples/`；最终文件位于本目录。
`motion-checks.json` 保存每段动画的数值检查：四肢长度、循环首尾位置。数值通过不代表动作专业审核通过。
本目录 `validation.json` 是本次交付的验证结果：360 帧无画面边缘裁切，三个闭环检查通过，六个媒体文件完整解码通过。

## 肌群与动作参考

以下来源仅用于核对文字知识，没有复制其中的图像或动画：

- 深蹲的股四头肌和臀大肌共同参与膝、髋伸展：[ACE 对深蹲与髋推的讨论](https://www.acefitness.org/continuing-education/certified/november-2019/7403/understanding-the-barbell-hip-thrust/)。
- 卧推的胸部目标与多关节推举：[NASM Barbell Bench Press](https://www.nasm.org/resource-center/exercise-library/barbell-bench-press)。
- 窄握划船的背阔肌与中背目标：[NASM Seated Machine Row: Close Grip](https://www.nasm.org/resource-center/exercise-library/seated-machine-row-close-grip)。此来源是器械划船说明，用于核对肌群；本样片采用绳索与独立握把，没有复制其器械轨迹。

## 环境检查

本机存在 Blender 和 ffmpeg。制作时，当前 Codex 会话没有暴露 Blender MCP 工具，常用端口 9876 无监听，已检查的 Blender 用户配置内也未找到名称含 MCP 的插件文件。这不足以排除 MCP 安装在其他配置中的可能性。
本次通过 Blender 本地 Python 接口完成，未修改用户 MCP 配置。
