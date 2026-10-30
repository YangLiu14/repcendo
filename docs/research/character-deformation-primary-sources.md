# 人体骨骼动画与网格形变：一手资料调研

调研日期：2026-10-29。范围：正常的人体动画制作方法、常见失真来源及验证顺序。本文不判断 Repcendo 当前脚本的具体根因，也不修改模型或动画。以下“资料事实”来自官方文档、原论文或标准组织；“工程建议”是据此提出的项目方案。

## 1. 核心判断

人体动画至少有三个不同问题：**骨架如何摆姿势、网格如何跟随骨架、极端姿势下如何保持人体形状**。IK 负责第一个问题；蒙皮权重与 LBS/DQ 负责第二个；局部修形、辅助骨骼或姿态驱动修正处理第三个。把它们统称为“骨架算法”会掩盖故障来源。Blender 官方分别提供 IK、Armature modifier 和关节 corrective shape key 工作流。[IK](https://docs.blender.org/manual/en/5.0/animation/constraints/tracking/ik_solver.html)、[Armature](https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/armature.html)、[关节修形示例](https://docs.blender.org/manual/en/dev/animation/drivers/workflow_examples.html)

**工程建议：**首先验收同一人物在标准关节测试下的形变，再复用到动作库。碰撞检测是另一项验收：无穿模不能证明肢体比例、关节体积或运动方向正确。也不能用平滑网格的方式把碰撞指标降下来，就视为人物质量合格。

## 2. 正常控制层：控制骨架、变形骨架、局部坐标

控制骨架向动画作者提供手脚目标、肘膝方向、身体姿态等操作接口；变形骨架向蒙皮提供最终骨骼变换。两者可以位于同一个 Armature 中，但职责不同。Rigify 是这种分层的一个官方实例：meta-rig 对齐人物后，生成控制、机构和 deform bones，并提供 FK/IK 与次级变形控制。它是可选实现，不意味着更换插件就会自动修复模型。[Blender Rigify](https://docs.blender.org/manual/en/2.81/addons/rigging/rigify.html)

IK 根据末端目标计算整条骨链的旋转；Pole Target 确定链的转向，例如肘部朝哪边。Stretch 会允许骨骼缩放以达到目标。**工程建议：**健身演示默认固定肢体长度；到不了目标时调整握距、器械或身体位置，而非悄悄拉长肢体。显式规定手掌朝向、肘膝弯曲平面和关节允许范围。Blender 的普通 Limit Rotation 不约束 IK 求解结果，应使用骨骼 IK 面板的限制；不能只加一个旋转限制就认为约束已生效。[IK 选项](https://docs.blender.org/manual/en/5.0/animation/constraints/tracking/ik_solver.html)、[Limit Rotation 边界](https://docs.blender.org/manual/en/4.2/animation/constraints/transform/limit_rotation.html)

Bone roll 是绕骨骼本地 Y 轴的旋转，因此相同的“转 X 度”必须结合该骨的局部轴理解。Blender 的 `PoseBone.matrix_basis` 表示相对父骨与自身 rest bone 的位置、旋转和缩放；`PoseBone.matrix` 是约束、驱动器求值后的 Armature 对象空间矩阵。世界、Armature、父骨和 rest 空间不能混用。[Bone Roll](https://docs.blender.org/manual/en/3.6/animation/armatures/bones/editing/bone_roll.html)、[PoseBone API](https://docs.blender.org/api/3.0/bpy.types.PoseBone.html)

在统一的模型坐标约定下，LBS 的基本关系可写为：

```text
v_posed = Σ_j w_j · G_j(current) · inverse(G_j(bind)) · v_bind
Σ_j w_j = 1
```

`G` 为骨骼的全局变换，沿父子链组合局部变换得到；inverse bind 将顶点带回相应骨骼的绑定坐标。具体引擎还可能需要 mesh/object 空间转换。**不能直接把“当前矩阵”作为顶点变形矩阵，漏掉绑定变换；也不能将 Blender 的局部姿态增量当作 glTF 动画通道值照搬。** 应通过实际导出再导入验证坐标约定。[Khronos：Skins](https://github.khronos.org/glTF-Tutorials/gltfTutorial/gltfTutorial_020_Skins.html)、[Khronos：场景节点变换](https://github.khronos.org/glTF-Tutorials/gltfTutorial/gltfTutorial_004_ScenesNodes.html)

**工程建议：**关节中心要与人物结构吻合；先校准肩、肘、腕、髋、膝、踝和脚趾根部，再绑定。把脚掌、脚趾、踝部分开控制，不能假定一个脚部骨骼能表达所有跪姿接触方式。必要时用辅助 twist bones 分摊轴向扭转，但应以测试证明需要，而非一味增加骨骼数。

## 3. 网格与权重是基础资产，不是每个动作的临时补丁

Blender 官方说明：自动权重使用 bone heat 计算影响，在复杂骨架或网格中可能分配到不希望影响的部位；此时需要手工调整。它是绑定起点，不是动作质量认证。[Armature Deform Parent / Automatic Weights](https://docs.blender.org/manual/sr/4.2/animation/armatures/skinning/parenting.html)

`Normalize All` 使每个顶点各组权重总和为 1；`Normalize` 只是把单个组的最大值缩放到 1，两者不能互换。**工程建议：**只对实际 deform groups 检查归一化，排除用于修改器遮罩等非骨骼组；检查无权重点、左右串权重、衣褶与相邻肢体误绑定、关节过硬分区。[Blender Editing Weights](https://docs.blender.org/manual/en/2.80/sculpt_paint/weight_paint/editing.html)

雕刻或生成模型的静态外观好看，并不保证适合弯曲。官方建议需要形变的网格评估 retopology；自动 remesh 通常不产生适合动画的最终拓扑。**工程建议：**观察肘、膝、踝的线框和跨关节边流，必要时局部重拓扑后转移细节与权重；不能仅凭面数多或全四边形宣布可动画。[Retopology](https://docs.blender.org/manual/en/3.0/modeling/meshes/retopology.html)、[Blender Remeshing / Retopology](https://docs.blender.org/UATEST/manual/en/dev/modeling/meshes/retopology.html)

## 4. LBS 与 DQ：需要比较，但不能包治百病

LBS 对多个骨骼变换加权求和。即使每个骨骼变换都是刚体变换，混合矩阵也不一定是刚体变换，因此会出现旋转处缩瘪与“糖纸扭结”。Kavan 等人的原论文给出了 180° 扭转时两个等权影响使截面塌陷的例子，并提出用 dual quaternion blending 改善这类旋转混合。[Kavan et al. 2008 原论文，§2.2](https://users.cs.utah.edu/~ladislav/kavan08geometric/kavan08geometric.pdf)

Blender 的 Preserve Volume 使用四元数方式改善旋转导致的体积损失；官方也明确提示跨越相对 rest 180° 时可能出现不连续。DQ 作者说明它选择较短的旋转路径，因此存在 flipping 边界，scale/shear 也需额外处理。**工程建议：**将 LBS 与 Preserve Volume 做相同姿势、相同权重的单变量对照；不要把人物是否正确归结为一个开关。错误关节中心、错权重、错骨长和错误动作目标都不会被蒙皮混合方式自动识别或纠正。[Blender Preserve Volume](https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/armature.html)、[作者的实现与限制](https://users.cs.utah.edu/~ladislav/dq/index.html)

历史参考：Magnenat-Thalmann、Laperrière、Thalmann 的 1988 年论文研究了关节相关局部形变与抓握；本文用 Kavan 2008 的明确公式解释现代 LBS，不把早期论文中的所有方法等同于今天某个实现。[Graphics Interface 原论文与出版信息](https://graphicsinterface.org/proceedings/gi1988/gi1988-4/)

## 5. 三种“修形”必须区分

| 方法 | 实际作用 | 适用边界 |
| --- | --- | --- |
| 普通 Smooth modifier | 顶点向拓扑邻点平均位置移动，重复执行就是反复做几何模糊 | 不知道人体关节结构，也不参考正确姿势；不应作为人体塌陷的主修复方法 |
| Corrective Smooth modifier | 以 rest state 为参考修正受扭曲区域，通常放在 Armature 后 | 是局部辅助；官方明确它仍可能损失体积，需正确 rest/bind 参考 |
| 姿态驱动 corrective shape keys / PSD | 为指定姿态制作目标形状，再按关节姿态驱动其影响 | 适合肘膝折叠、肩臀轮廓等；需验收中间姿态和多关节组合 |

普通 Smooth 的迭代次数是几何平均执行次数，**不是** IK 或肌肉模拟的精度。由其算法可推知，大量重复可能削弱截面、轮廓和细节；这是算法推论，不是对当前项目根因的断言。[Blender Smooth：Algorithm 与 Repeat](https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/smooth.html)

Corrective Smooth 的 `Rest Source` 可以用原始坐标或绑定坐标；前面有增加几何的修改器时需正确绑定。其 `Only Smooth` 只是预览内部平滑，不能把该模式当成已经进行了校正。它仍不理解肘、脚踝应具有何种解剖形状。[Blender Corrective Smooth](https://docs.blender.org/manual/en/4.2/modeling/modifiers/deform/corrective_smooth.html)

PSD 原论文将姿态参数映射到物体局部坐标中的形变位移；Blender 官方给出了通过 shape key 修正肘部、通过 driver 随姿态平滑启用的例子。**工程建议：**先稳定骨架和权重，仍有局部缺陷再做姿态修形；不要用修形掩盖整根前臂被缩放、脚骨翻转等控制层错误。单关节 driver 只是简化方案，复杂组合不能假定线性相加始终合理。[Lewis et al. 2000 原论文](https://doi.org/10.1145/344779.344862)、[Blender Shape Key Drivers](https://docs.blender.org/manual/en/dev/animation/drivers/workflow_examples.html)

## 6. 建议落地的正常 pipeline

以下为工程方案，不是文档声称的唯一行业标准：

1. **建立人物基线。** 固定 mesh、rest pose、骨架版本、单位/轴向与绑定关系；保留原始生成资产。分别验证男女模型，不假定不同体型可直接共用权重。
2. **校准骨架。** 定义关节中心、本地轴、固定骨长、变形骨与控制骨。搭建手脚 IK、Pole Targets、旋转限制与明确的接触模式；姿势求解和蒙皮分开记录。
3. **验收绑定。** 在同一 rest pose 做单关节动作范围测试：肘屈伸、前臂扭转、肩抬举、髋屈伸、膝屈曲、踝活动和脚趾弯曲。观察线框、权重、截面和多视角轮廓。
4. **验证蒙皮。** 暂时关闭后置几何补丁，比较 LBS / Preserve Volume。每次只改变一个因素，先定位控制、绑定、混合或后处理中的哪一层引入问题。
5. **添加有限修正。** 必要时局部重拓扑、调整权重、加入辅助骨或姿态修形。需要 Corrective Smooth 时使用正确 rest/bind 参考，保留与未修正结果的可比较版本。
6. **再制作动作与接触。** 从经验证的 rig 出发，控制动作节奏、器械、握持、脚底与膝部接触；不为每个动作另写一套改变人体基础比例的蒙皮补丁。
7. **双重质检。** 同时检查穿模与形变；先用报告标出坏帧，再人工检查。不能只看少数关键帧或单一镜头。
8. **验收交付格式。** 离线视频检查渲染帧即可验证输出形状；如果以后实时导出 glTF，需在目标播放器验证最终蒙皮与 morph/动画求值。Blender driver、修改器的视觉结果不能假定由一个骨骼动画文件自动完整复现。

建议给现有碰撞门禁补充：骨长与非预期缩放、静止姿态回归、关节角与突跳、局部截面/边长变化、脚掌与手部轮廓、多视角关键帧检查。阈值应从已人工通过的基线确定；不是把全身变成刚体，也不是禁止关节的一切自然压缩。

## 7. 当前问题如何验证，避免凭截图猜根因

建议先选用户标出的两类动作建立对照，不立刻重做全部 19 个动作：

- 固定同一帧、同一模型、同一骨姿态，比较“当前完整栈”“仅 Armature”“仅 Armature + Preserve Volume”。
- 如果骨骼自身的轴向、长度或姿态已经异常，先查控制/空间转换；如果骨架正常但皮肤异常，查绑定、权重与蒙皮；如果只有加后处理才异常，逐个启用修改器定位。
- 对脚掌与肘部另做中立姿态和独立关节转动测试；截面检查应使用对应部位的局部坐标，而非只看全局包围盒。
- 记录哪些现象被某项更改解决、哪些仍存在。更换 DQ 后“看上去更圆”并不能证明接触、关节朝向或解剖形状已正确。

调研限制：部分 Blender `latest` 页面直接抓取失败，引用使用可检索的官方页面内容及明确版本；旧版 API/手册引用只用于稳定概念，实际参数与求值行为仍应以项目安装的 Blender 版本测试确认。本轮没有声称已经解决或通过这些验收。
