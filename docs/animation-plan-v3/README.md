# 四日计划动作动画

对应 `workout_plans/recomposition-4day-2026-10-28-v3.json` 的正式动作条目。四周复用 19 个唯一动作，男女各一版；卧推与坐姿划船保留在 v2 目录。本轮 38 个场景统一进行穿模修复、全帧检测和重新渲染。旧深蹲继续保留，因此 App 完整目录为 20 个动作、40 段视频。

| 训练日 | 动作 |
|---|---|
| 周一 · 胸＋三头＋腹 | 杠铃卧推、上斜哑铃卧推、蝴蝶机夹胸、绳索三头下压、跪姿绳索卷腹 |
| 周二 · 背＋二头 | 高位下拉、坐姿绳索划船、绳索直臂下拉、哑铃弯举 |
| 周三 · 腿部综合 | 45 度腿举、杠铃罗马尼亚硬拉、坐姿腿弯举、坐姿腿屈伸、器械站姿提踵 |
| 周四 · 肩＋腹 | 坐姿哑铃推举、哑铃侧平举、蝴蝶机反向飞鸟、反向卷腹、死虫式 |

`coverage.json` 保存计划 ID、版本、动作 ID 和训练日，不包含个人重量反馈。备注中的步行、骑车和热身不是正式次数型动作条目，不在这次 19 项覆盖范围内。

## 资产

- `male/`、`female/`：每个新增动作的 `.blend` 可编辑场景、`.mp4` 视频、`-poster.png` 封面、`-motion-checks.json` 烘焙诊断。
- MP4：H.264 / yuv420p / 1280×960 / 24 fps，静音、支持循环与 iOS 离线播放。
- 普通动作 120 帧 / 5 秒；死虫式 192 帧 / 8 秒，包含左右交替。
- `index.html`：按训练日筛选的 19 项预览，男女切换，可见视频才自动播放，点击全屏。
- `validation.json`：覆盖率、完整解码、逐帧边界、最终媒体及场景摘要。
- `hand-grip-validation.json`：真实手部网格包覆、五指接触和握持漂移。
- `scene-validation.json`：真实网格闭环、静止脚部、杠铃轴线、垫面和台阶接触检查。
- `collision-validation.json`：38 个场景、4,742 个检测帧的双向器械碰撞与非局部身体自交检查，固定 2 mm 容差。
- `collision-baseline.json`：修复前的诊断基线；仅四个关键姿势，不作为导出依据。
- `*-media.json`：视频与封面到已通过检测场景的版本凭据。

肌群材质沿用选定的希腊雕塑模型，标示体表区域，不表示激活强度，也不把浅层材质当作完整解剖层。器械为原创简化模型，不对应某个厂商的机器尺寸。技术与画面检查不等于教练对所有动作的专业审定。

## 制作与复现

动作元数据在 `Scripts/animation_samples/plan_exercises.py`，动作轨迹和器械适配器在 `plan_motions.py`。旧三个动作的实现保持独立。

```sh
# 完整流程；使用已安装 Pillow 的 Python。
python3 Scripts/animation_samples/plan_pipeline.py
# 保留手工调整的场景，只验证、渲染并导出。
python3 Scripts/animation_samples/plan_pipeline.py --from-scenes

# 单独调整一个动作时，先查看关键姿势，再跑全部帧检测。
python3 Scripts/animation_samples/render_plan.py --bake --review --exercise leg_press
python3 Scripts/animation_samples/validate_collisions.py --exercise leg_press
python3 Scripts/animation_samples/render_plan.py --exercise leg_press
```


渲染器当前默认 `/opt/homebrew/bin/blender`，两个并行场景、每场景四线程。新增场景根据 17 个关键时点的实际网格自动取景，预留 3.5% 边距；最终仍逐帧检查 alpha 边界。帧序列和日志位于被忽略的 `build/animation-plan-v3/`。断点续渲染对照 `.blend` SHA-256；场景变化会清除该场景的旧帧。修改动作代码后先 `--bake-only`，重新通过全帧穿模检测后再渲染；修改渲染设置后需清除对应帧目录。不要同时对同一场景烘焙和渲染。

### 动作和接触细节

- 上斜凳沿用计划的约 30° 倾角；握点随各自哑铃运动。
- 三头下压使用分叉绳索；固定上臂，以伸肘完成动作。
- 高位下拉在身前下拉，保留压腿垫，移除遮挡背阔肌的靠背。
- 直臂下拉保持小幅固定屈肘；硬拉通过髋后移和躯干前倾完成，不从地面起杠。
- 共享杠杆的两只手使用同一水平轴线；指骨闭合并应用既有握杆接触修形。
- 腿举使用 45° 导轨、随脚底移动的踏板及滑架；腿弯举与腿屈伸的滚垫跟随小腿，不共用相反动作的轨迹。
- 提踵根据真实脚底顶点校正台阶接触；仰卧动作使用张开的手。反向卷腹包含骨盆抬起，死虫式交替伸展对侧手脚。
- 仰卧时，雕塑上背的突出体积需要独立垫面接触修形：仅对蒙皮后穿入垫面的底面压平，节点保留在交付场景中，源人物不改动。骨盆、脊柱和四肢仍使用原烘焙轨迹；脚部移动和关节轨迹不靠此修形处理。

动作轨迹参考了 NASM 的动作说明：
[坐姿腿弯举](https://www.nasm.org/resource-center/exercise-library/seated-leg-curl)、
[死虫式](https://www.nasm.org/resource-center/exercise-library/dead-bug)、
[杠铃罗马尼亚硬拉](https://www.nasm.org/resource-center/exercise-library/romanian-deadlift-barbell)、
[上斜哑铃卧推](https://www.nasm.org/resource-center/exercise-library/two-arm-incline-dumbbell-chest-press)。动画、器械及人物资产均由本项目的制作流程生成，没有复制这些页面的视频或图片。

App 的动作目录同步补齐了这批动作的中文名称，可以按「腿举」「死虫式」等名称搜索；计划中的 displayName、动作 ID、目标组数和训练记录不改动。

穿模检测的覆盖范围、局部关节/指间接触限制及门禁规则见 [动画制作流水线](../animation-pipeline.md#穿模检测与-19-动作生产流程)。自动检测不替代近景和多视角目视审核。


### 死虫式肩腋修正（2026-10-29）

男女两版已更新局部姿态 Shape Keys，减轻抬臂时腋下与侧肋的大面积拉伸，保留原骨架轨迹、网格、UV 和肌群纹理。新增 `dead_bug-strain.json` 完整 193 帧回归门禁、`dead_bug-shoulder-corrective.json` 制作记录、`dead_bug-preservation.json` 保留项检查及肩腋近景审核。原穿模容差不变；局部雕塑折痕仍保留。此修正仅校准当前死虫式，详见 [缺陷与验收记录](known-issues/dead-bug-axilla/README.md)。

### 蝴蝶机结构修正（2026-10-30）

夹胸、反向飞鸟的男女四版按 [Life Fitness SS-FLY 官方产品照片](https://www.lifefitness.com/en-us/catalog/strength-training/selectorized/insignia-series-pectoral-fly-rear-deltoid) 的结构重新制作。顶部竖直转轴驱动横向定长摆臂与下垂握臂，补齐胸背靠垫、配重塔及底座；手部通过 IK 匹配器械圆弧。保留本项目的配色和简化形式，不是厂家尺寸/内部传动的工程复刻。

`pec-deck-validation.json` 保存四版全 121 帧机构检查；`equipment-review/` 保存主镜头/侧面三阶段照片对照证据。参考记录见 [pec-deck.json](../equipment-references/pec-deck.json)。其余旧器械仍需逐项完成照片对照。
