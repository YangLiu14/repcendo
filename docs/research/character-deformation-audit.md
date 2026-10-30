# Repcendo 人物形变调研与现有流程诊断

> 本文是修复前的诊断快照，表格中的「当前」指当时的旧资产。后续实施与最终证据见 [形变修复记录](../animation-plan-v3/deformation-repair-notes.md)。

日期：2026-10-29。任务：调查脚踝、手肘等身体畸变的原因与正确制作流程。本轮仅研究与只读场景对照，没有修复或重新发布动画。

## 结论

骨架驱动人物的技术路线没有问题，但当前实现还不是经过验收的角色动画系统。自动生成的绑定、脚本修改的关节与权重、程序化姿态、强平滑补丁被叠加使用，缺少对每层形变质量的独立验证。不能把“无穿模”“骨长不变”“手握住器械”等同于身体形状正确。

已经证实：**强普通 Smooth 会加重硬拉肘部收缩；它不是卷腹脚部异常的原因。** 当前两个场景使用 LBS；改成 DQ / Preserve Volume 并没有消除所有畸变。尚未证实脚踝的唯一根因，不能据截图把全部问题归咎于一个蒙皮算法。

正常方法、一手资料与算法边界见 [一手资料调研](character-deformation-primary-sources.md)。

## 正常系统如何工作

1. **网格与绑定基线：**模型需要适合关节弯曲的拓扑；关节中心、本地轴、rest pose、变形骨和权重先固定并验收。自动权重只是起点。
2. **控制层：**FK 直接指定关节旋转；IK 用手脚目标反求骨链姿势。肘膝方向、前臂扭转、脚掌方向和关节范围仍需明确。末端位置正确，不代表骨骼朝向正确。
3. **蒙皮层：**按照绑定姿态与当前姿态之间的变换，再用权重让表面跟随骨架。LBS 是常用方法，但旋转混合可导致缩瘪；DQ 改善此类问题，不能理解或纠正错误人体姿势。
4. **修形层：**在正确的骨架、权重、蒙皮基础上，必要时加入辅助骨、局部重拓扑、姿态驱动 shape keys。Corrective Smooth 有 rest 参考；普通 Smooth 只是反复平均邻点，二者不能混称。
5. **验收层：**分别验证人体形变、动作与接触、穿模，再检查输出视频或实时播放器。几何指标只能筛出疑似坏帧，不能单独证明解剖正确。

相关来源：[Blender 自动权重](https://docs.blender.org/manual/sr/4.2/animation/armatures/skinning/parenting.html)、[IK](https://docs.blender.org/manual/en/5.0/animation/constraints/tracking/ik_solver.html)、[Khronos 蒙皮与绑定矩阵](https://github.khronos.org/glTF-Tutorials/gltfTutorial/gltfTutorial_020_Skins.html)、[DQ 作者说明](https://users.cs.utah.edu/~ladislav/dq/index.html)、[Smooth](https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/smooth.html)、[Corrective Smooth](https://docs.blender.org/manual/en/4.2/modeling/modifiers/deform/corrective_smooth.html)、[肘部 shape key driver 示例](https://docs.blender.org/manual/en/dev/animation/drivers/workflow_examples.html)。

## 代码中已确认的实现

| 位置 | 当前行为 | 判断 |
| --- | --- | --- |
| `Scripts/animation_samples/joint_correctives.py` | 使用 `SMOOTH`，factor=1，按部位重复 50–100 次；20–22 cm 半径的空间遮罩、8 cm 渐变；没有姿态角度驱动 | 不是基于姿态制作的关节修形；普通平滑会改变截面与细节 |
| `Scripts/animation_samples/build_sculpture_scene.py` | 动画构建时修改手腕/脚踝/脚趾的 rest 骨位置，并按坐标高度覆盖部分手脚权重 | 需要把这些操作纳入角色绑定验收；按高度分区不能证明权重符合关节结构 |
| 同上 `orient` / `setbone` | 构造方向坐标系、写入 PoseBone 矩阵，再烘焙位置和四元数 | 程序化求解本身合理；仍需检查坐标空间、本地轴、twist 与连续性，不能仅凭写矩阵就认定错误 |
| `Scripts/animation_samples/plan_motions.py` | 上臂与前臂分别通过最短方向旋转和弯曲平面定向 | 存在轴向扭转分配不协调的风险；当前实验尚未独立证明这是硬拉剩余扭曲的根因 |
| 同上 `leg` 的 `cable_crunch` | 小腿朝后；脚与脚趾使用固定 `rx(3.85)` 旋转，没有独立脚趾屈曲或踝部相对角度验收 | 需要验证脚掌接触模式、脚骨与小腿的相对姿势。3.85 rad 是脚本的全局旋转参数，不能直接称为人体踝关节角度 |
| `collision_audit.py` / `collision_gate.py` | 验证接触和交叠，并限制陈旧报告使用 | 未验收截面、关节轮廓、扭转分配和解剖合理性；通过不能代表动画质量合格 |

本次打开的 RDL 保存场景仍使用一个 `Elbow and knee fold relaxation` 修改器，卷腹保存场景是两个独立修改器。它们与当前生成脚本的组织方式有差别，因此以下实测针对保存场景本身，不假定所有场景完全一致。

## 只读对照实验

环境：本机 Blender 5.2.1 LTS。输入：男性 `rdl.blend`、`cable_crunch.blend`，各第 61 帧。同一动作的四个版本保持模型、姿势、相机、灯光一致：

- current：保存场景原状态。
- no_smooth：只关闭普通 Smooth。
- dq_only：只启用 Armature Preserve Volume。
- no_smooth_dq：关闭 Smooth 并启用 Preserve Volume，用于观察两者组合；不将组合结果当成单变量证据。

![同姿态对照：上排硬拉肘部，下排卷腹脚部；左为当前，中为关闭 Smooth，右为关闭 Smooth 并启用 DQ](deformation-evidence/comparison.jpg)

| 检查 | 实测 | 能说明什么 |
| --- | --- | --- |
| 两场景当前蒙皮 | `use_deform_preserve_volume=false` | 当前使用默认线性混合，值得对比 DQ，但不能直接归因 |
| 变形骨权重总和 | 最小 0.99999984，最大 1.00000009 | 在浮点精度内归一化；不证明每块皮肤分给了正确骨骼 |
| 受查肢体骨变换 | 变形矩阵奇异值接近 1；受查肘腕膝踝趾关节父子端点差远小于 1 mm | 这两个采样姿态没有明显骨骼缩放或链条断开；不能外推全片、全部动作 |
| 硬拉关闭 Smooth | 肘周区域顶点平均变化 15.7 mm、最大 36.2 mm；明显细缩减轻，仍有扭曲 | 平滑是当前肘部外观恶化的一个已确认因素，基础绑定/姿态问题仍待查 |
| 卷腹关闭 Smooth | 脚部区域顶点变化为 0 | 此帧脚部异常不由这些 Smooth 修改器造成 |
| 卷腹仅改 DQ | 脚部区域平均变化 0.79 mm、最大 11.75 mm；轮廓仍不合理 | 一个保体积开关不能解决该脚部问题 |

肘部诊断区域为 rest 空间内距两侧前臂骨头部 16 cm 内的顶点；脚部区域为原网格坐标 z < 0.15 的顶点。报告另存区域边长比的分位数，用于比较形变分布，**不是人体合格阈值，也不是体积测量**。全部数据见 [probe.json](deformation-evidence/probe.json)。

只读探针见 [probe.py](deformation-evidence/probe.py)，从项目根目录可运行：

```sh
/opt/homebrew/bin/blender -b -t 2 --python-exit-code 1 --python docs/research/deformation-evidence/probe.py
```

输出到 `build/deformation-research/`；探针只改变加载后的内存场景，不保存 `.blend`。实验后两份输入场景 SHA-256 与开始时一致。没有覆盖模型、视频、App 资源或修改生产脚本。

## 尚未证实的部分

- 脚部是错误目标朝向、脚踝关节中心、坐标阈值权重还是原始拓扑主导，需要独立关节测试区分；可能是组合问题。
- 肘部去掉平滑后仍然扭曲，需检查前臂轴向旋转与权重。当前不能说更换 IK 或 DQ 就能完整修复。
- 网格以三角面为主不等于不能动画；应根据关节附近边流和形变测试决定是否局部重拓扑，不能凭面类型直接重做全身。
- 本次不是全动画验收，只检查了两个男性动作的代表帧。没有证明其余帧、女性模型或其他动作正常。

## 推荐后续实施顺序

1. 暂停扩大动作数量，将两个人物的干净绑定版本确定为基线；暂时隔离强平滑等补丁，保留旧版用于对照。
2. 做每个人物的关节测试片：肘屈伸和前臂扭转、肩抬举、髋膝屈伸、踝活动与脚趾弯曲。正侧背视角检查，记录网格、骨架、权重和姿态。
3. 按证据修正关节中心/本地轴与姿态，再调整权重和必要的局部拓扑；比较 LBS/DQ。不要用大范围平滑掩盖错位。
4. 只为剩余的局部形变制作辅助骨或姿态驱动修形，验证中间姿势与组合姿势。
5. 先验收用户指出的卷腹和硬拉，男女版本均通过后，再把同一绑定系统应用到全部 19 个动作。
6. 将“形变检查”和“穿模检查”并列为出片条件。加入非预期缩放、关节突跳、局部边长/截面异常的提示，并保留人工多视角审查；阈值来自已通过的角色基线。

这轮调查纠正了上一轮验收标准：碰撞报告通过仍可伴随严重身体畸变。后续应修复绑定与控制的基础问题，而不是继续围绕碰撞数值叠加表面补丁。
