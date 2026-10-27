# 希腊雕塑人物 · 3D 资产 v1

2026-10-27。男、女两份模型已通过 Tripo 生成并绑定 Mixamo 人体骨架，可在 Blender 中继续制作动作。

## 文件

| 内容 | 男性 | 女性 |
|---|---|---|
| 已选原始三视图 | [greek-male.png](../../character-concepts/greek-sculptures/greek-male.png) | [greek-female.png](../../character-concepts/greek-sculptures/greek-female.png) |
| 单人物建模输入 | [male-front.png](inputs/male-front.png) | [female-front.png](inputs/female-front.png) |
| 无骨架 GLB | [greek-male-source.glb](male/greek-male-source.glb) | [greek-female-source.glb](female/greek-female-source.glb) |
| 带骨架 GLB | [greek-male-rigged.glb](male/greek-male-rigged.glb) | [greek-female-rigged.glb](female/greek-female-rigged.glb) |
| 可编辑 Blender | [greek-male.blend](male/greek-male.blend) | [greek-female.blend](female/greek-female.blend) |
| 基础关节变形视频 | [rig-check.mp4](male/rig-check.mp4) | [rig-check.mp4](female/rig-check.mp4) |
| 检查报告 | [inspection.json](male/inspection/inspection.json) | [inspection.json](female/inspection/inspection.json) |

[并排动图](rig-check-pair.gif) · [预览页面](index.html) · [完整任务与文件校验清单](manifest.json)

女性交付版本已按用户要求抹平胸部衣料下的局部尖锐凸起，保留整体轮廓和主要衣褶。修整同步到无骨架 GLB、带骨架 GLB、Blender 与预览；原始 Tripo 下载仅留在 `female/source/`、`female/rig/` 作为回溯资料，不作为当前交付文件。选定概念三视图也保持原档。

局部修整使用保持 UV 接缝连续的网格平滑，未改变拓扑、UV 或蒙皮权重；修改 1,284 个顶点，未产生新的云端费用。[修整记录](female/refined/refinement.json) · [修整后侧面近景](female/refined/chest-side.png)。

## 管线和参数

复用 Whimphony 已验证的官方 CLI 管线：选定概念图 → 单人物正面输入 → Tripo 高清网格/PBR → 免费 rig-check → Mixamo 自动骨架和蒙皮 → Blender 检查。

- 原始三视图原样保存，SHA-256 已记录。单人物输入使用内置 `image_gen` 整理；[完整输入整理提示词](inputs/prompt.txt)。
- `tripo-cli@0.5.2`，通过既有本地授权调用。仓库中不保存凭证。
- 生成模型：`v3.1-20260211`；`face_limit=50000`，`texture=true`、`pbr=true`，几何和材质质量均为 `detailed`；种子 `20261027`。
- 骨架：复用已验证的 `v1.0-20240301`、`rig_type=biped`、`spec=mixamo`、`out_format=glb`。
- 两个人物各用 60 credits 生成 + 25 credits 绑定；适配检测免费。合计 **170 credits**，余额从 615 变为 445。
- 任务 ID、服务端回执、生成参数和文件哈希均在本目录保留；临时下载 URL 已从日志移除，离线资产不依赖 URL 有效期。

参考官方文档：[图生模型](https://developers.tripo3d.ai/en/docs/generation-image-to-model)、[人体骨架](https://developers.tripo3d.ai/en/docs/animations-rig)。

## 实际验证

| 指标 | 男性 | 女性 |
|---|---:|---:|
| 三角面 | 48,498 | 49,278 |
| 顶点 | 27,438 | 27,816 |
| 骨架节点（含根节点） | 23 | 23 |
| 蒙皮 | 1 | 1 |
| 无权重顶点 | 0 | 0 |
| 带骨架 GLB | 10.45 MiB | 9.88 MiB |

Blender 5.2.1 已实际导入并渲染正、背、左右侧视图。检查了双臂抬起、双肘弯曲、双髋和双膝弯曲；变形顶点坐标有限、没有异常飞散，权重和误差小于 1e-4。GLB 包含网格、骨架、蒙皮、UV 和内嵌纹理；`.blend` 已打包纹理。

`preview-skeleton.png` 的橙色线是实际骨骼位置向正面平面的投影，便于查看关节位置，不是新增解剖结构。

## 如何继续做动作

1. 用 Blender 打开对应 `.blend`。选择 `Armature`，进入 Pose Mode，通过 `mixamorig:*` 骨骼编辑姿势。
2. 文件停在第 1 帧中立姿势；时间线 1–97 帧包含 `QA_JointFlexion_NOT_Exercise` 检查动作。播放可以查看蒙皮。制作正式动作时新建 Action，保留该检查动作作为参考。
3. 带骨架 GLB 保留原始中立姿态，未把检查动画混入正式模型。可导入其他支持 glTF 蒙皮的工具继续编辑，或按 Mixamo 骨骼名做动画重定向。
4. 模型保持 Tripo 标准化尺寸（Blender 中高约 0.98 单位），在 Blender 中面朝 +X、Z 向上；glTF 导出遵循其 Y 向上坐标。匹配器械前需统一人物与器械比例，整体缩放骨架和网格，避免只缩放网格。

## 当前边界

- 这是可摆姿势的基础身体资产。23 节点骨架不含独立手指、面部表情或 IK 控制器；精细握杠需要补充手指绑定。
- 自动三角网格和蒙皮在大角度肩髋屈伸时可能需要人工修权重或矫正形态。当前测试不是完整动作范围认证。
- 单正面输入重建了侧背面细节，女性后脑发髻被简化。选定三视图完整保留，可用于后续精修。
- 检查视频只演示骨架驱动，不是健身动作教学。具体动作的脚底固定、器械接触、动作轨迹以及主要肌群高亮尚未制作。
- 当前为制作母版，保留高清纹理；尚未做 iOS 实机渲染性能、纹理压缩和多模型同屏验证，也未加入 App 包。

## 本地复验

下面的命令只读取本地文件，不会创建云端任务或消耗 credits：

```sh
blender --background --threads 6 --python-exit-code 1 \
  --python Scripts/character_assets/inspect_character.py -- \
  --source docs/character-assets/greek-athletes-v1/male/rig/model.glb \
  --out build/greek-male-check --pose-check

python3 Scripts/character_assets/finalize_assets.py
```

女性当前模型使用 `female/refined/rig.glb`。局部修整可通过 `blender --background --python-exit-code 1 --python Scripts/character_assets/refine_female_chest.py` 重现；它始终从原始下载读取，不会重复叠加修整。检查脚本只加载已有模型并检验/渲染。
