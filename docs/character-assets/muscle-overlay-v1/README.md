# 希腊雕塑 · 可选肌群贴图 v1

基于已选男女雕塑制作的写实纤维材质与肌群区域示意。保留原人物网格、UV 和 Mixamo 骨架，支持单独显露 17 个主要肌群。女性使用已抹平胸部局部凸起的修整版，不覆盖上一轮白色人物资产。

[打开交互预览](http://127.0.0.1:8770/character-assets/muscle-overlay-v1/)：可旋转、缩放、切换男女、选择肌群，并播放骨架跟随测试。页面全部依赖保存在本地，不需要 CDN。

## 交付内容

| 资产 | 男性 | 女性 |
|---|---|---|
| 可编辑 Blender，含肌群显示开关 | [greek-male-muscles.blend](male/greek-male-muscles.blend) | [greek-female-muscles.blend](female/greek-female-muscles.blend) |
| 带骨架 GLB，18 个独立命名材质 | [greek-male-muscles.glb](male/greek-male-muscles.glb) | [greek-female-muscles.glb](female/greek-female-muscles.glb) |
| 2048² 肌群颜色图 | [muscle-albedo.png](male/textures/muscle-albedo.png) | [muscle-albedo.png](female/textures/muscle-albedo.png) |
| 2048² 切线空间法线图 | [muscle-normal.png](male/textures/muscle-normal.png) | [muscle-normal.png](female/textures/muscle-normal.png) |
| 2048² 肌群 ID 图 | [muscle-id.png](male/textures/muscle-id.png) | [muscle-id.png](female/textures/muscle-id.png) |
| 2048² 柔边覆盖图 | [muscle-coverage.png](male/textures/muscle-coverage.png) | [muscle-coverage.png](female/textures/muscle-coverage.png) |
| 原始白色底图 | [marble-basecolor.png](male/textures/marble-basecolor.png) | [marble-basecolor.png](female/textures/marble-basecolor.png) |
| 17 张独立灰度遮罩 | [masks/](male/textures/masks/) | [masks/](female/textures/masks/) |
| 正面效果 | [all-front.png](male/all-front.png) | [all-front.png](female/all-front.png) |
| 背面效果 | [all-back.png](male/all-back.png) | [all-back.png](female/all-back.png) |
| 区域、面数与预设清单 | [manifest.json](male/manifest.json) | [manifest.json](female/manifest.json) |

颜色图在两个人物各自原始 UV 上烘焙，不能互换。模型与贴图已经匹配，可以直接使用整套文件。

## 为什么采用这个表示方式

- 默认显示白色雕塑；选定区域显露暗红纤维，保留白色关节、肌腱附近和非目标区域，减少视觉干扰。
- 肌群边界和纤维方向分别处理。胸大肌采用向外侧汇聚的扇状映射，手臂/腿以长轴为主，背阔肌和腹外斜肌使用斜向映射。
- 所有材质沿用现有顶点与蒙皮，动画不会因为独立肌肉壳层而发生层间滑动或穿插。它也不会模拟肌肉膨胀、收缩体积或筋膜滑动。
- 本版是**体表位置示意**，不是逐块剥离的解剖模型。男女共用肌群名称，但按各自网格和骨架生成独立贴图。

## 肌群 ID

`0` 为白色雕塑；其余 ID 的材质名是 `Muscle_<两位ID>_<key>`。

| ID | key | 区域 |
|---:|---|---|
| 1 | pectoralis_major | 胸大肌 |
| 2 | deltoid_anterior | 三角肌前束 |
| 3 | deltoid_lateral | 三角肌中束 |
| 4 | deltoid_posterior | 三角肌后束 |
| 5 | biceps_brachii | 肱二头肌 |
| 6 | triceps_brachii | 肱三头肌 |
| 7 | forearm_flexors | 前臂屈肌群（合并示意） |
| 8 | forearm_extensors | 前臂伸肌群（合并示意） |
| 9 | rectus_abdominis | 腹直肌 |
| 10 | external_oblique | 腹外斜肌 |
| 11 | trapezius | 斜方肌 |
| 12 | latissimus_dorsi | 背阔肌 |
| 13 | gluteus_maximus | 臀大肌 |
| 14 | quadriceps | 股四头肌群（表面区域，未暴露深层股中间肌） |
| 15 | hamstrings | 腘绳肌群（合并示意） |
| 16 | gastrocnemius | 腓肠肌 |
| 17 | tibialis_anterior | 胫骨前肌 |

左右侧当前合并控制。尚未制作独立左右 ID、深层肌肉和完整全身肌肉系统。

## 如何控制显示

### Blender

打开对应 `.blend`，选择 `Armature`，在对象自定义属性中找到上述 `key`。`0` 隐藏，`1` 显示，中间值可渐变。驱动器同时控制颜色混合和肌肉法线强度。修改属性后更新视图即可。原骨架仍可在 Pose Mode 摆姿势。

### GLB / 应用接入

GLB 默认显示全部肌群。每个肌群是一份独立命名材质，应用可以按材质 ID 换成肌肉或白色材质；本地 `viewer.js` 展示了此方式。GLB 不包含 Blender 驱动器，显示开关应由应用实现。

更适合后续移动端优化的方式是把材质合并，由一个 shader 读取 `muscle-id.png` 并用 18 项显示强度数组控制：

```text
id = round(sampleNearestLinear(muscleID, uv).r * 255)
color = mix(marbleAlbedo, muscleAlbedo, selectedStrength[id])
```

ID 图必须按 **Non-Color / linear** 数据读取，使用最近邻采样，避免 sRGB 转换和 mipmap 插值改变编号。颜色图按 sRGB 读取，法线图和灰度遮罩按 linear 读取。颜色图已经包含边缘与白色底图的柔和混合，不必再叠一次覆盖图。

独立遮罩用于自定义 shader、重绘或重新烘焙。每张只包含该 ID 的区域和柔边；覆盖图是这些区域的合并覆盖强度。

预览中的“卧推示意”“划船示意”“深蹲示意”只展示一组相关肌群，不是完整动作分析，也不表示主次肌群的定量激活。正式动作数据可保存 `primaryMuscles` 与 `secondaryMuscles`，分别映射到这些稳定 key。

## 验证和当前边界

- 两套导出均保留 23 骨架节点和蒙皮属性；三角面分别为 48,498 / 49,278，未增加人体几何。
- 每套包含 18 个命名材质，ID 图含 0–17，17 张独立遮罩非空且没有跨 ID 污染；GLB 纹理均内嵌。[校验结果](validation.json)。
- 两份导出 GLB 再次导入 Blender，确认无未加权顶点，并验证肩、肘、髋、膝弯曲后的坐标与位移。[男性变形检查](male/deformation-validation.json)、[女性变形检查](female/deformation-validation.json)。
- 已检查男女正背面、胸/背/腿局部切换。预览支持实时旋转与骨架驱动。测试片段不是正式训练动画。
- 区域轮廓是结合参考资料与现有网格制作的近似轮廓；纤维走向经过艺术化简化，未经过专业解剖审核。
- 女性胸肌是胸大肌所在区域向外表面的示意投影，**乳房不等于肌肉**；衣物区域以贴图覆盖，仍保留原衣褶几何。若要展示真正的皮下肌肉，需要另建解剖层。
- 17 个肌群并不覆盖所有动作涉及的肌肉。深层旋转袖、菱形肌等未伪装成可见表面区域；当前也不模拟肌肉长度/横截面变化。
- 18 个材质分段用于编辑和验证；尚未做 iOS 实机性能测试或 App 接入。手机正式版宜改用单材质 ID shader，并按实测选择分辨率/压缩格式。

## 来源与复现

解剖位置参考 OpenStax《Anatomy and Physiology 2e》：[11.5 肩带与上肢](https://openstax.org/books/anatomy-and-physiology-2e/pages/11-5-muscles-of-the-pectoral-girdle-and-upper-limbs)、[11.6 骨盆与下肢](https://openstax.org/books/anatomy-and-physiology-2e/pages/11-6-appendicular-muscles-of-the-pelvic-girdle-and-lower-limbs)。使用其解剖知识作参考，没有复制教材插图或上游 GIF。

纤维颜色素材使用内置 `image_gen` 新生成：[原始素材](shared/fiber-albedo.png)、[完整提示词与模式](shared/fiber-prompt.txt)。这是写实风格的生成材质，不是组织摄影。Blender 根据区域方向映射并烘焙到各人物原 UV，法线由浅浮雕材质烘焙。未调用 Tripo，未增加 Tripo credits 消耗。

```sh
blender --background --threads 6 --python-exit-code 1 \
  --python Scripts/character_assets/build_muscle_overlay.py -- --sex male --size 2048
# 女性改为 --sex female
python3 Scripts/character_assets/validate_muscle_assets.py
python3 -m http.server 8770 --bind 127.0.0.1 --directory docs
```

校验脚本需要 NumPy 与 Pillow；生成脚本使用 Blender 自带 Python。预览使用本地 Three.js 0.180.0，许可证保留在 `vendor/three/LICENSE`。
