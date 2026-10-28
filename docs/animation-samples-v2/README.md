# 雕塑动作样片 v2

2026-10-28。用已选希腊雕塑人物和肌肉纤维材质，重做深蹲、卧推、坐姿划船。男女各三段，均为 5 秒循环，保留可编辑 Blender 源文件。此次交付独立样片，尚未接入 iOS App。

[打开男女切换预览](http://127.0.0.1:8770/animation-samples-v2/) · [概览](overview.png) · [验证结果](validation.json)

| 动作 | 主要标记 | 男性 | 女性 |
|---|---|---|---|
| 杠铃深蹲 · 0043 | 股四头肌、臀大肌 | [MP4](male/squat.mp4) / [GIF](male/squat.gif) / [Blender](male/squat.blend) | [MP4](female/squat.mp4) / [GIF](female/squat.gif) / [Blender](female/squat.blend) |
| 杠铃卧推 · 0025 | 胸大肌 | [MP4](male/bench.mp4) / [GIF](male/bench.gif) / [Blender](male/bench.blend) | [MP4](female/bench.mp4) / [GIF](female/bench.gif) / [Blender](female/bench.blend) |
| 窄握坐姿绳索划船 · 0861 | 背阔肌、斜方肌表面区域 | [MP4](male/row.mp4) / [GIF](male/row.gif) / [Blender](male/row.blend) | [MP4](female/row.mp4) / [GIF](female/row.gif) / [Blender](female/row.blend) |

[手部近景](hand-grips-overview.png) · [可复用五指骨架资产](../character-assets/hand-rig-v1/README.md)

## 人物与动作

- 人物使用本项目已经选定的男女雕塑网格、原 UV、身体骨架和肌群材质，并扩展为 53 根骨骼（新增 30 根手指骨骼）；女性沿用胸部局部凸起已抹平的版本。原人物源资产保持原档。
- 在动画副本中校准自动骨架的手腕和脚踝端点，调整手脚远端蒙皮，为五指各增加三节骨骼并绑定蒙皮，校准掌心与杆轴，四指包杆、拇指对握。接触形态键用于防止皮肤穿杆，主要弯曲由真实指骨完成。
- 动作按每个人物的实际肢段长度重新求解双骨关节位置。脚部目标保持固定；杠铃和握把与握持目标同步运动。不是把旧分段人偶逐个替换为独立网格。
- 器械采用本项目原创建模方式；动作轨迹重新生成，没有导入、提取或描摹上游 GIF 的姿态数据。
- Blender 5.2.1 LTS，EEVEE 渲染。`.blend` 保留 121 帧骨架/器械关键帧与打包纹理；播放范围为 1–120，121 用于验证闭环。第 1 帧为准备姿势，第 61 帧为底部/收缩位置。

## 深蹲肩颈与落杠修正

新增 [正背面对照](squat-shoulder-comparison.png)、[男女三视角](squat-shoulder-views.png) 和 [独立接触检查](squat-shoulder-validation.json)。侧面检查图隐藏配重片，便于观察杠轴和肩颈之间的位置；正式动作视频保留完整器械。

旧版的问题有三部分：固定的杠铃偏移落在肩背内部；男性原模型的后侧上背体积偏大；抬臂时不合适的上臂权重和旋转使轮廓进一步扭曲。当前副本修整后侧上背轮廓，将颈后错误的上臂权重移回躯干，并移除深蹲上臂由不稳定肘平面引入的额外扭转。

落杠采用高杠示意，依据各自网格的上背表面寻找直径 28 mm 杠轴的后侧相切位置。躯干前倾、髋部站位和手臂姿势同步求解，使杠铃轨迹保持在足中部附近。肩颈形体与蒙皮也同步更新到可复用人物副本，源资产仍保留。

验证使用变形后的三角网格，检查男女各 121 帧（含闭环帧）中的杠轴表面和轴心，利用三方向射线奇偶性确认是否位于体内，避免凹陷附近最近面法线造成误判；同时检查双侧支撑间隙和颈后表面相对躯干的偏移。该验证专门补足旧版仅检查四肢长度和握点的不足。

落杠位置的文字依据：[NASM Squats and Deadlifts](https://trainer.nasm.org/hubfs/NASM_Free%20Guide_Squats%20and%20Deadlifts.pdf?hsLang=en) 中的 high-bar upper trapezius 描述。没有复制其影像或动作数据。

## 肌群表现

红色纤维表示本段突出显示的体表肌群位置，不表示激活百分比或贡献比例。右侧正背面图补足动作视角的遮挡。

- 卧推仍会涉及肱三头肌和三角肌前束，本片保持胸大肌为主要视觉标记。
- 划船使用背阔肌与现有斜方肌表面贴图。当前资产没有独立深层菱形肌，因此没有把它画成可见的独立解剖层。
- 贴图属于近似体表区域；衣物处仍保留衣褶几何，不是皮下肌肉实体或收缩体积模拟。
- 这些是动作制作样片，尚未经过专业教练审核；自动蒙皮在深度屈伸处仍可能出现体积损失和衣褶拉伸。

## 输出规格与验证

- MP4：1280×960，24 fps，120 帧，H.264，5 秒。
- GIF：960×720，16 fps，80 帧，5 秒，无限循环。
- 六段均检查骨架闭环、四肢长度误差和握持目标误差；另在 60 个关键手部姿势上检查实际蒙皮表面的环向包覆、各指接近杆面、穿杆和相对器械的滑移，验证旋转指骨确实改变网格。手部检查见 `hand-grip-validation.json`；检查所有渲染帧的透明边界，防止画面边缘裁切，并完整解码输出媒体。
- 关键姿势检查覆盖每段的准备、中间、底部/收缩和回程位置。数值与媒体检查结果记录在 `validation.json`，并保留各动作的 `*-motion-checks.json`。

## 复现

完整的统一入口、依赖与新增动作步骤见 [原创动作制作流水线](../animation-pipeline.md)。建议使用 `python3 Scripts/animation_samples/pipeline.py --mode full` 同步重建资产并运行全部检查；下方保留单独调用方式。

在项目根目录执行，需要本地 Blender、ffmpeg，以及含 Pillow 的 Python：

```sh
# 男女版本与正背面肌群参考图
python3 Scripts/animation_samples/render_sculpture_samples.py

# 中文卡片、MP4、GIF 和预览页面
python3 Scripts/animation_samples/package_sculpture_samples.py

# 实际深蹲肩颈和杠轴接触验证
blender --background --python-exit-code 1 --python Scripts/animation_samples/verify_squat_shoulders.py

# 实际手部网格与指骨控制验证
blender --background --python-exit-code 1 --python Scripts/animation_samples/verify_hand_grips.py

# 媒体、边界与闭环验证
python3 Scripts/animation_samples/verify_sculpture_samples.py

python3 -m http.server 8770 --bind 127.0.0.1 --directory docs
```

手部近景与可复用骨架导出：

```sh
blender --background --python Scripts/animation_samples/render_hand_closeups.py
blender --background --python Scripts/character_assets/export_hand_rig.py
```

只制作关键姿势预览：

```sh
python3 Scripts/animation_samples/render_sculpture_samples.py --previews-only
python3 Scripts/animation_samples/package_sculpture_samples.py --preview
```

中间帧与日志放在已忽略的 `build/animation-samples-v2/`。上一版人偶示意保存在 [animation-samples](../animation-samples/)，可用于对比。完整人物和肌群材质来源见 [肌群资产说明](../character-assets/muscle-overlay-v1/README.md)。本次没有重新调用 Tripo。

## 动作知识参考

仅参考文字知识核对目标肌群与动作关系，没有复制参考网站的图片、视频或动画：

- [ACE Exercise Library](https://www.acefitness.org/resources/everyone/exercise-library/)
- [NASM Barbell Bench Press](https://www.nasm.org/resource-center/exercise-library/barbell-bench-press)
- [NASM Seated Machine Row: Close Grip](https://www.nasm.org/resource-center/exercise-library/seated-machine-row-close-grip)
