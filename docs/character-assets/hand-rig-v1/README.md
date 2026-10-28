# 希腊雕塑 · 五指骨架 v1

2026-10-28。保留已选男女雕塑的几何风格、肌群 UV 和女性胸部修整，新增可独立控制的五指骨骼。源资产 `greek-athletes-v1` 与 `muscle-overlay-v1` 原档保留；本目录是新的动作制作版本。

| 人物 | 可编辑源文件 | 通用 3D 资产 |
|---|---|---|
| 男性 | [Blender](male/greek-male-hand-rig.blend) | [GLB](male/greek-male-hand-rig.glb) |
| 女性 | [Blender](female/greek-female-hand-rig.blend) | [GLB](female/greek-female-hand-rig.glb) |

## 如何控制

- 原有 23 根身体骨骼加 30 根手指骨骼，共 53 根。
- 命名：`mixamorig:LeftHandIndex1`，依次更换 `Left/Right`、`Thumb/Index/Middle/Ring/Pinky`、`1/2/3`。
- 进入 Pose Mode 后可分别旋转指骨。骨骼已经分配蒙皮权重，并非只添加空骨骼。
- `Hands_Open_Close` 动作为张手到闭握的制作参考：1/21/121 帧张手，61/81 帧闭握。GLB 将手指与形态键合并为一段动画。
- `Left_Grip_Clearance`、`Right_Grip_Clearance` 是适配直径 28 mm 握杆的接触修形。改变握法、张手或改变杆径时应归零并重新校正。逐指弯曲由骨骼完成。
- Blender 文件保留原来的肌群显示自定义属性。GLB 使用白色雕塑材质；原肌群 UV 和材质分区仍保留，可复用 `muscle-overlay-v1` 的肌群贴图。

## 制作与边界

重新校准手腕与掌心握点，为每根手指绑定三节 FK 骨骼；四指包覆与拇指对握分别求解。焊接导入模型的重合顶点以消除接缝，保留面角 UV。脚踝与脚底蒙皮沿用动作样片中的修正。

当前指骨位置和权重专门适配这两个模型，不是通用自动绑骨工具。手指是 FK，暂不包含逐指 IK 或自动碰撞求解。原模型低模拓扑在极近镜头仍可看到部分指关节棱角；其他手势需要单独调整和检查。

[更新后的三个动作，男女共六段](../../animation-samples-v2/) · [实际握持验证](../../animation-samples-v2/hand-grip-validation.json)

生成脚本：`Scripts/character_assets/hand_rig.py`、`Scripts/character_assets/export_hand_rig.py`。没有调用 Tripo 或产生新的云端生成费用。

## 肩颈修订（2026-10-28）

本目录人物副本现包含后侧上背轮廓修整和肩颈蒙皮修正，防止抬臂时颈后顶点被上臂拉走。五指骨骼和张手/闭握动作仍保留。实现见 `Scripts/character_assets/shoulder_rig.py`；深蹲中的上臂旋转与落杠位置由动作脚本控制。
