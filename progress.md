# 工作日志

## 2026-10-27
- 完成仓库与工具链检查；阅读 UI 和文件规划技能。
- 确定实现范围、离线架构和三页导航。
- 已请求用户自行处理 Xcode 许可，未代用户接受协议。
- 用户完成许可确认；核心模块编译和 iOS 模拟器构建成功。
- 实现三页 SwiftUI UI、导入预览、每组记录、恢复草稿、休息计时、动作替换、历史和反馈导出。
- 12 项核心测试通过。开始在新建的 Repcendo QA 模拟器执行 UI 流程测试。
- 生成 1,324 条精简文字动作数据、四周格式示例和可直接打开的 Xcode 工程。
- 核心测试增至 13 项，通过；新增 plan-check 校验 CLI 和 Codex 计划生成说明。
- iPhone 17 Pro 上完整 UI 测试与导航测试通过，实际完成系统文件保存。
- 修复了错误弹窗关闭训练页的问题；测试等待模态过渡完成，避免过早点击。
- 已查看普通/最大字体/横屏截图；改进大字体输入间距与次要文字对比度。
- 小屏 iPhone SE 回归正在执行；另将使用模拟器系统设置验证深色和减少动态效果。
- iPhone SE 两项 UI case 通过；Xcode 在收尾阶段停滞，已终止该 runner 并清理其专用设备。
- iPad mini 系统深色、减少动态效果开启：完整流程与导航两项测试通过，xcodebuild TEST SUCCEEDED。
- 已检查深色、大字体、横屏实际截图，保存于 docs/screenshots。
- 工程引用、plist、示例资源一致性和 Git whitespace 检查通过；上游 submodule 保持干净。
- 测试专用模拟器已清理。实现完成，使用步骤在 README，计划交接规则在 docs/codex-plans.md。

## 原创样片
- 用户授权制作深蹲、卧推、坐姿划船三段样片，并标明主要训练肌群的位置。
- 使用现有文件规划技能继续跟踪；确认 Blender/ffmpeg 可运行，开始制作原创建模脚本。
- 首轮姿势预览发现划船脚位超出腿长约束，已收回脚位并调整脚踏；改进贴合表面的股四头肌标记、卧推握距和镜头留白。
- 完成三个原创建模场景与 360 帧渲染；各动作 121 帧数值检查无四肢长度错误、循环首尾位置误差为 0。开始制作中文肌群侧栏与可播放预览页。
- 已验证预览页播放入口；媒体编码时长为 5 秒。边界扫描发现深蹲底座在原始帧底缘轻微裁切，已下移取景中心并重新渲染。
- 三个 5 秒 MP4（1280×960 / 24fps）与 GIF（960×720 / 16fps）已导出；保留 .blend 和生成脚本。
- 360 帧边界检查、3 个闭环检查、6 个媒体完整解码均通过；已人工查看每个动作 4 个关键姿势、最终中文标注版式，并测试预览页播放。
- 最终结果在 docs/animation-samples/；本地预览 http://127.0.0.1:8766/ 已打开并保留。此次未修改 iOS App 或签名设置，未接入手机 App，未提交或推送。

## 人物概念图
- 用户反馈程序化分段人偶不满意，改为概念图 → Tripo 生成 → 骨骼绑定流程。当前仅制作概念图，待用户选定造型。
- 使用内置 imagegen 生成三套独立三视图：A 自然运动员、B 风格化运动角色、C 哑光人体雕塑。已检查全身正/侧/背视图和基本造型一致性。
- 原图与完整提示词保存于 docs/character-concepts/；此阶段没有生成 3D 模型，也没有修改 App。

- 用户确认保留第一轮白色雕塑图（文件 c-sculpted-human.png），但明确要求新一轮不要以白模为基准。
- 第二轮通过内置 imagegen 独立生成 D 街头火花、E 轨道教练、F 力量捣蛋鬼三套彩色三视图；未引用上一轮图片。原图与提示词保存在 docs/character-concepts/round-2/。

- 用户重新选择白色雕塑感觉，要求希腊雕塑风格男性/女性配套形象。已使用内置 imagegen 生成两张正侧背三视图，检查全身、发型、材质和服装一致性；保存于 docs/character-concepts/greek-sculptures/。

## 2026-10-27 希腊雕塑 3D 交付
- 保存男女概念三视图，内置 image_gen 整理单人物正面输入。
- 使用既有授权 Tripo CLI 生成两套高清网格；免费双足检测通过；各绑定 23 节点 Mixamo 骨架。
- Blender 实测所有顶点都有权重；肩肘髋膝变形有限且无异常飞散，正背侧面人工检查。
- 按用户后续要求修整女性胸部局部凸起，保持 UV 接缝和蒙皮；重新验证、导出 GLB/.blend/MP4/GIF。
- 交付目录 docs/character-assets/greek-athletes-v1；本地预览 http://127.0.0.1:8770/character-assets/greek-athletes-v1/ （server session 50782）。
- 总计 170 credits，余额 445。手指、IK、具体运动轨迹/器械接触/肌群高亮待后续动作制作；未加入 App，未 commit/push。

## 肌群材质与交互预览交付
- 使用内置 image_gen 生成纤维材质，以 Blender 烘焙到男女原 UV，输出颜色/法线/ID/覆盖图，各 17 张独立遮罩。
- 17 个肌群按材质独立控制，保留 23 节点骨架；保存 GLB 和带显示驱动器的 .blend。
- 校正了原骨架上臂中心的偏差与小腿遮罩断裂，完成男女正背面检查。
- 独立校验 GLB、三角面、骨架、34 张遮罩、ID 数据通过；再次导入导出模型的肩肘髋膝变形检查通过。
- 本地 Three.js 预览通过男女切换、胸部单选、全选、卧推示意、恢复白模与骨架测试开关验证，保留 IAB 标签 4。
- 交付 docs/character-assets/muscle-overlay-v1；预览 http://127.0.0.1:8770/character-assets/muscle-overlay-v1/ 。无新增 Tripo 消耗；未改动原人物交付模型或 iOS App。

## 雕塑动作样片 v2 · 制作中
- 已建立男女版本深蹲、卧推、划船的 121 帧闭环动作与器械场景。
- 在动画副本中修正腕踝端点、手脚远端权重，添加握持修形；原角色资产保持原档。
- 人工查看男女三动作关键收缩/底部姿势，修正手臂和小腿长度超限目标、脚底约束与照明；开始完整渲染。

## 雕塑动作样片 v2 · 完成交付
- 男女六段 MP4（1280×960 / 24fps）和 GIF（960×720 / 16fps），每段 5 秒；保留 .blend 与打包纹理。
- 卧推平台边界裁切修正后，720 帧透明边界检查、6 个骨架闭环与 12 次完整媒体解码均通过。
- 六场景五个关键帧的实际变形网格有限，脚底表面最大漂移约 2.8e-7m；握持骨架参考点误差小于 1e-4m。
- 查看全部 24 个关键姿势；浏览器验证男女切换后每个视频 5 秒、readyState=4、paused=false，之后全部暂停成功。
- 交付 docs/animation-samples-v2，预览 http://127.0.0.1:8770/animation-samples-v2/ ，IAB 标签 5 保留。旧版和原角色资产原档保留。
- 本次未接入 iOS、未调用 Tripo、未新建 Git commit。

## 2026-10-28 · 修正手部未握杆
- 按 diagnosing-bugs 流程复现旧卧推的实际表面包覆缺失，保留诊断在忽略的 `build/hand-rig-review/`。
- 新增 `hand_rig.py`（逐指骨骼、权重、闭握和接触修形），更新三个动作的腕部与器械接触逻辑。
- 男女各三段已重渲染；输出 12 张实际手部近景。新增预览页手部近景入口与媒体版本参数，避免显示缓存的旧动画。
- 新增独立五指骨架资产与张手/闭握参考动作，GLB 重导入验证通过。新增 `verify_hand_grips.py` 实际握持检查通过；脚底表面漂移检查通过。
- 本次未修改 iOS 代码，未调用云端生成，未 commit/push。
- 最终交付检查完成：720 帧渲染边界、6 段循环、12 个完整 MP4/GIF 解码通过。浏览器男女各三段播放正常，均加载 `?v=hands1` 资源。
- 预览页已展开手部近景；实际浏览器截图保存为 `docs/animation-samples-v2/hand-rig-preview.png`。原链接继续可用。

## 2026-10-28 · 深蹲肩颈与落杠修正
- 独立复现杠铃穿肩和颈后异常隆起，区分原模型体积、错误上臂蒙皮与扭转问题。
- 增加肩背轮廓/蒙皮修正模块和实际表面落杠求解；深蹲上臂使用稳定摆动，髋位、躯干和握杆同步更新。
- 更新用于动画的男女副本及可复用手指骨架资产；保留原始人物/肌群源档。
- 全部六段重新渲染保持人物一致，新增 12 张肩颈多视角检查图与前后对照。深蹲 242 个姿势的真实网格接触检查通过；60 个关键手部姿势、脚底稳定及导出 GLB 重新导入验证通过。
- 本次没有修改 iOS 源码、调用云端生成、commit 或 push。
- 最终验证：242 个深蹲姿势检测到的杠轴深度穿入为 0，双侧支撑间隙最大约 2.87 mm；颈后网格相对躯干的偏移小于 0.001 mm。720 帧边界和 12 个完整视频/GIF 解码检查通过。
- 浏览器已验证男女各三段均播放最新 `?v=shoulders2` 媒体；页面默认展开肩颈/落杠修正前后对照。截图保存为 `docs/animation-samples-v2/shoulder-revision-preview.png`。

## 2026-10-28 · 流水线整理与提交
- 统一格式化新增脚本并核对 AST 不变，抽取动作目录；增加 `pipeline.py` 的 full / verify / dry-run、依赖预检、逐阶段日志和失败停止。
- 完整流水线运行 `20261028T041418936621Z` 的 10 个阶段全部通过：重渲染、手部近景、肩颈检查图、骨架导出、打包，以及五类验证。
- 242 个深蹲姿势接触、60 个关键手部姿势、脚底稳定、GLB 重导入、720 帧边界和 12 个完整媒体解码检查全部通过。
- 新增 `docs/animation-pipeline.md`，记录新增动作需要的轨迹/器械/接触实现与目视审核；README 链接已补齐。
- 提交范围包含本轮 v2 成品、源场景、可复用骨架、代码与记录；中间帧、日志、Blender 备份仍被忽略。未修改 App 或上游 submodule，未 push。

## 2026-10-28 · 按训练计划补齐动画
- 已读取指定 v3 计划，提取所有周的唯一正式动作 19 个，确认现有覆盖 2 个，计划制作其余 17 个男女版本。
- 本轮开始前工作树仅 Plans/、workout_plans/ 未跟踪，现有 App/动画已提交 2d09575。
- 采用 planning-with-files-zh 记录清单、制作和验证进度；不生成或调整训练计划。

### Plan animation implementation / key-pose pass
- Added 17 motion/equipment adapters, 34 baked Blender scenes, resumable rendering and per-frame kinematic diagnostics.
- Rendered and visually inspected 136 quarter-cycle key poses across both sexes; correcting equipment placement before final renders.
- Existing v2 scenes and plan JSON preserved.

### Plan animation final export
- Completed 17 new motions × 2 characters, plus the existing bench and row entries in a grouped 19-exercise preview.
- Fixed rigid-bar alignment, leg machine handles/sled supports, floor/step contact, and scene framing from evaluated geometry.
- Final scene and hand-surface checks passed; all 4,224 rendered frames and 34 encoded videos passed verification. Synced all 20 total motions / 40 videos into the offline App resources.
- Core package: 14 tests passed. Final App build and UI regression are running.

### Completed / 2026-10-29
- App build succeeded with final framed media. Verified copied catalog and all 40 bundled video/poster SHA-256 values in the built `.app`.
- Core tests: 14 passed. Full UI suite: 4 passed, runner TEST SUCCEEDED (`build/UITests-20261029-001542.xcresult`). Covers both sexes, autoplay/replay, fullscreen, background pause, 8-second dead-bug loop, workout-demo entry and retained weight entry.
- Test fixture now handles the sample plan and draft left by the existing import/large-text test; no user data is reset.
- Added the 14 missing Chinese exercise names through `prepare_resources.py`; all 19 plan motions are searchable in Chinese.
- Preview: http://192.168.1.8:8770/animation-plan-v3/ ; all plan actions grouped by day, both characters, viewport fullscreen. IAB tab retained.
- No plan edits, submodule changes, commit or push during this task.

### Collision repair request / 2026-10-29
- User reports widespread intersections in the 19-plan-motion set. Beginning geometric collision repro and baseline audit before further visual changes.
- Existing uncommitted plan-animation work and personal plan files preserved. No commit requested.
- Implemented collision_audit.py and deterministic regression fixtures. Added surface-fitting adapters, hand topology refinement, local joint correctives, and movement/hardware corrections; iterating with key-frame audits before final all-frame gate.
- Added fail-closed render/package/App export checks for complete per-frame reports, scene SHA-256, validator SHA-256 and media provenance. No new videos have been published while scene fixes are in progress.
- First full audit covered 28 scenes; after a targeted male-pushdown grip corrective all 28 passed. Second full audit found 3 remaining female shoulder transition cases; other 7 scenes passed. Rendering begins only for passing, hash-matched scenes.
- Grip regressions passed: 30 closed-hand plan scenes and 6 legacy scenes. Scene loop/rigid-bar/foot-support checks passed for all 34 new scenes before the final 3 local shoulder adjustments (these will be rechecked).
- Final full collision gate passed: 38 scenes, 4,742 sampled frames including loop closure; zero findings above the 2 mm tolerance in the documented detection scope. Female fly/dead-bug intermediate shoulder folds repaired locally and re-audited.
- All original source sculpture files and the pinned exercise submodule remain unchanged. Rendering 4,704 output frames; packaging and App resource verification are next.

### Collision repair delivery complete / 2026-10-29
- Re-rendered and repackaged all 19 plan motions × 2 characters (4,704 rendered frames). The original squat remains unchanged, so the App still contains 20 motions / 40 videos.
- Final collision evidence: all 38 scenes / 4,742 frames passed; reports include source and validator SHA-256. Preserved the original 4-pose diagnostic baseline (31/38 scenes failed; 547 equipment findings).
- Geometry fixtures: 5 passed; export-gate regressions: 3 passed. Final grip checks passed for 30 closed-hand new scenes and all 6 legacy scenes. Loop, planted-foot, rigid-bar and mat/step checks passed for all 34 new scenes.
- Final media validation: 4,224 new frames / 34 MP4s plus 720 legacy frames / 6 MP4+GIF pairs passed full decode and frame-edge checks. The 480 repaired legacy bench/row frames are included in the 4,704 plan-frame total.
- App resources synced. iOS simulator build succeeded at build/CollisionAppBuild/Build/Products/Debug-iphonesimulator/Repcendo.app. Verified its catalog and all 80 video/poster hashes against the source asset catalog.
- Preview refreshed and read back in IAB: 19 entries, updated media-content revision URLs, visible videos playing muted and looping without media errors. Preview remains http://192.168.1.8:8770/animation-plan-v3/ . Phone installation requires a new Xcode Run; no phone data or existing simulator was reset.
- No commit/push requested or performed. Existing unrelated changes and personal workout plans retained.

### 人物形变实施 / 2026-10-29
- 用户已授权按调研计划修复基础绑定、先验证两个样本，再推广 19 动作。
- 使用 diagnosing-bugs 的差分回归和 planning-with-files-zh 的阶段记录。已有对照复现 Smooth 加重硬拉肘部塌陷，但卷腹脚异常不受 Smooth 影响。
- 首先建立固定姿势的关节朝向/局部网格检查，避免把无穿模当作人体形变合格；保留旧版视频直到新产物通过检查。
- 旧男性硬拉第61帧的 deformation_audit 已复现失败：50次强平滑、双侧脚权重影响小腿、肘部额外轴向扭转127.6°/143.3°。这是新增检查的红样本，非碰撞检查。
- 候选版本将前臂朝向沿上臂运输，关闭普通 Smooth，使用 Blender Preserve Volume；手部接触逆变换同步支持 DQ，并与 Blender 实际求值比对，误差小于1微米。
- 初次脚部重分配发现 Blender 顶点组成员是可变视图；逐项删除导致索引漂移。改为先缓存组索引，再删除。候选检查识别到了权重总和异常，旧资源未覆盖。
- 临时探针曾因 Quaternion 无 xyz 属性、bpy collection不支持步长切片和 inspect.py命名遮蔽标准库报错，均已在诊断目录修正。Bone.vector 属于父空间，数值探针统一使用 tail_local-head_local。
- 四个样本（男女硬拉/卷腹）的全帧机械形变检查通过；各5关键帧碰撞检查通过。已检查近景和动作整体姿态，接下来是全循环碰撞与全部动作多视角复核。
- 已生成男女中立绑定和8组独立关节测试片；新增形变导出门禁必须同时有完整自动报告及与场景hash匹配的多视角视觉检查，不会自动把检测通过写成视觉通过。
- 提取人物准备模块时遗漏source变量、Blender 5.2的EEVEE枚举改名及本地化节点名导致一次失败，均修正后重新生成候选；错误未影响生产资源。
- 第一轮全38候选筛查捕获死虫式辅助扭转骨的约178°突跳：空手不应沿世界固定握杆坐标，已让空手跟随前臂，保留有器械动作的握持约束。
- 膝部采用关节中心一致的连续权重过渡；通过对照 .035/.05/.065/.08 模型单位半宽，男性 .08 在90°屈膝时消除了局部交叠且保留膝部轮廓。女性使用较窄 .065，独立复核。
- 其余修正针对控制/器械：划船加入肩胛前伸随动，提踵把手连杆改为向掌外绕行，肩推底部避免额外过屈肘，腿弯举/腿举端点保持正常屈膝范围。
- 同步新增表面边长变化分位统计与疑似坏帧提示；这些是视觉检查线索，不宣称是解剖质量分数。候选阶段报告与最终文件需hash一致，正在重跑。

### 形变修复实施：逐项验收
- 共 38 段完成全循环形变自动检查，并实际查看正/侧/背关键帧证据（含报告挑出的可疑帧）。保存审核记录与图片哈希；普通强 Smooth 不再使用。
- 独立关节测试男女各 256 帧完成。极端膝踝仍保留源雕塑局部折痕，记录为适用范围限制；没有把压力测试当作解剖/动作认证。
- 全循环碰撞复查发现男性绳索下压第 13/109 帧的食指接触问题，37 段通过。扩大单一握持修正至 19 mm 未可靠解决，回归阻断了导出；局部半径试验正在验证 18 mm，并继续完整循环检查。未改变 2 mm 碰撞容差或跳过器械。
- 34 个新增场景的支撑/闭环检查、全部闭合握持动作的手部表面检查通过；下压重烘焙后会再次核验来源哈希。
- 下压最终版本采用保留厚度的位移及独立左右修正；完整 121 帧碰撞通过，手部接触检查也重新通过。已更新该动作的形变证据和视觉记录。
- 最终候选的 38 段形变与碰撞门禁通过；34 段新动作场景支撑/闭环与所有闭合手握持检查通过。新绑定测试新增了左右 Shape Key 独立性回归，男女均通过。最终媒体渲染进行中。


### 形变修复交付完成
- 38 段场景、4,704 输出帧完成正式渲染与打包，候选场景/报告/多视角证据已推广到 docs；App 同步 20 动作/40 视频（含未改的原深蹲）。
- 4,742 帧完整碰撞和形变检查通过；三视角证据与场景 SHA 匹配。34 新视频完整解码和 4,224 帧边界检查通过；原三动作的 720 帧/6 循环/12 个 MP4+GIF 解码检查通过。
- 新增形变门禁 5 项、碰撞门禁 3 项测试通过；男女绑定与独立左右握持修正回归通过；旧三动作 60 个握姿及 6 场景变形检查通过。
- App 同步时捕获包导入路径问题，已修正 relative/direct 两种调用方式并重试成功；最终 xcodebuild BUILD SUCCEEDED。构建产物中全部 81 个媒体资源文件与源目录哈希一致。
- 本地预览服务器原未运行，已在 127.0.0.1:8770 恢复；浏览器实际打开新页面并确认硬拉新视频 readyState=4、正常播放、5秒循环和全屏展示。未在本轮重新安装到真机，也没有重跑不涉及改动的 UI 全套测试。
- 已更新制作文档与最终修复说明。极端关节测试的源雕塑局部折痕继续作为限制保留，不宣称专业动作/解剖认证。本轮未提交 Git。

## 2026-10-29 卷腹反向握持修复完成
- 旧男女场景第 61 帧分别测得 163.28° / 165.77° 补偿轴转；最终方向检测器可复现失败。只改握把基准的第一试版仍有约 60° 折腕，也被新检查拒绝。
- 以相对掌向和可倾斜握把重新求解，拳心位置固定；男女全循环最大轴转 27.52° / 31.63°，折腕 <0.03°。原地烘焙并替换仅两段 cable_crunch，其他场景保留。
- 新增全 121 帧握持方向门禁，连接正式渲染/打包/App 同步；方向、形变、穿模和实际指骨/皮肤接触均通过。审核包含正侧背和器械可见四阶段近景，实际查看后登记。
- 形变/握向门禁 9 项测试、碰撞门禁 3 项测试通过；34 新动作场景采样、全套握持回归和 4,224 个渲染帧资产检查通过。
- 两段 MP4/封面、预览缓存版本和 App 资源更新；iOS 模拟器 BUILD SUCCEEDED，构建包 81 个资源文件 SHA-256 与源目录一致。浏览器男女视频均确认新版哈希、readyState=4、自动循环、全屏可播。未重新安装手机。
- 旧反例与中间候选在 build/grip-direction/，正式证据在 docs/animation-plan-v3/。未提交 Git。

## 2026-10-29 死虫式肩腋问题：仍未修复
男女均已复现。垫面不是主因；权重、锁骨、蒙皮及姿态修正试验尚未获得可交付结果。撤回两项视觉验收，现有视频保留，生产门禁拒绝该动作。具体证据和未完成事项见 `docs/animation-plan-v3/known-issues/dead-bug-axilla/README.md`。不要在后续汇总中把前一轮的“19 动作通过”沿用为当前全部合格。

## 2026-10-29 全库制作启动
- 已阅读 AGENTS、制作流程、现有计划与缺陷记录，运行规划技能的 session-catchup；无遗漏上下文报告。
- 工作区有大量已有未提交文件，全部保留。确认 1,324 项文本动作与 20 项原创媒体目录，向用户说明男女双版本总量并询问完整库/当前训练计划范围。
- 开始制作可重跑的精确 ID 盘点，分别报告媒体存在、当前门禁通过、旧版和已撤回审核；不会自动批准或覆盖现有资源。
- 已新增 `Scripts/animation_samples/library_inventory.py` 并生成 `docs/animation-library/inventory.json`、`inventory.csv`：1,324 个唯一 ID、男女各一项，清单行数及映射验证通过。
- 实际调用现有碰撞/形变/视觉门禁，核对场景、媒体凭据、源视频与 App 视频/封面哈希：18 项当前检查通过、1 项旧版深蹲需纳入新检查、1 项死虫式阻断、1,304 项尚未实现。没有新生成动画，也没有把盘点清单当成成品。
- Python 语法检查通过；现有碰撞门禁 3 项、形变/握姿门禁 9 项回归通过。已有场景、视频、审核记录、App、训练计划和上游数据均未修改。
- 用户确认完整 1,324 项，按男女双版本分批制作验收。新增独立 library_exercises / library_motions / library_pipeline：复用角色、骨长求解与原始碰撞/形变引擎，按动作保存报告和视觉证据；旧检测器文件不变，不使既有审核凭据失效。
- 首批八个源场景完成初次烘焙，正在修复关键姿势问题。新增五项独立批次门禁测试，连同原 12 项回归全部通过。没有自动批准视觉审核。
- 第 001 批完成：0285、0310、0313、1678，男女各一版；普通动作 5 秒，交替弯举 8 秒。源场景、八段 MP4、封面、逐帧报告、多视角证据和交付收据位于 `docs/animation-library/`。
- 全帧检查捕获女性锤式弯举中间帧哑铃片/大腿接触（最大约 7.4 mm）和女性前平举肩部局部相交；调整该角色的手臂侧向间距并完整重查，未改检测容差。八个场景共 1,112 帧通过碰撞、机械形变、握姿/逐指接触、足底稳定和网格闭环；实际查看全部八项主镜头/正/侧/背/手部图后写入审核记录。
- 完成 1,104 输出帧；八个 MP4 逐一完整解码、H.264 / 1280×960 / 24 fps / 帧数检查及全帧 alpha 边界检查通过。
- 批次同步预检男女所有资产后再写入；保留原 20 项目录内容，逐一核验全部 96 个视频/封面哈希。修正默认全量同步可能丢掉新批次的集成问题。新增两项批次同步回归，验证失败时不写入半个批次、成功时保留无关项。
- 源数据保持 pinned、不复制上游媒体；通过 prepare_resources.py 加入四个中文名并修正 0313 的中立握文字。训练计划与实际记录不改动。
- 门禁/同步测试共 23 项、Core 14 项通过；工作区原形变门禁增加的死虫式测试保留。iOS 模拟器构建 BUILD SUCCEEDED，构建包 97 个动画资源文件与源码目录一致；没有安装或覆盖手机数据。
- 浏览器打开 http://127.0.0.1:8770/animation-library/，男女四项 readyState=4、时长 5/8/5/5 秒，实际验证男性锤式弯举与女性交替弯举播放；截图保存在 preview.png，预览标签保留。
- `batch-001.json` 记录交付与来源；inventory 已更新为 24 项已制作/已入包，其中 22 项当前门禁通过、旧深蹲 1 项、死虫式阻断 1 项。全库仍有 1,300 项待制作，不宣称整体完成。未 commit/push。


## 2026-10-29 死虫式肩腋姿态修正交付
- 原男性第 145 帧 p95=2.791、女性第 49 帧 p95=2.925 的反例已保存。局部表面松弛若没有体积引导会塌陷；单独换权重/蒙皮未能解决，因此保留原 Armature / DQ 并烘焙姿态修正。
- 新增 shoulder_volume / shoulder_contacts / bake_shoulder_correctives：24 个采样姿态、周期插值及逐帧 Shape Key 权重；男女校准体积引导，女性前肩衣褶随抬臂相位保护。只修当前死虫式，不称全局肩部绑定已重建。
- 全 193 帧肩腋 p95 最大值男性 1.79515、女性 1.79699，原阈值 1.8 不变；全帧碰撞沿用原 2 mm 容差，两版通过。原始坐标/UV 相同、骨姿态矩阵差异 0、闭环误差 0。
- 实际查看正侧背和肩腋近景，以及成品浏览器播放后重新登记两个场景的 accepted。大面积侧肋拉伸明显收回，局部雕塑折痕及衣褶仍保留；其余 36 个场景未重新制作。
- 两版 MP4/封面/来源凭据、预览缓存和 App 资源更新，完整逐帧拉伸门禁接入渲染/打包/同步。13 项形变门禁测试通过；全计划资产校验通过（19 项计划动作、34 个计划目录视频、4,224 帧）。旧资产验证器现兼容并校验已交付的全库批次，不再错误要求目录只能有旧 20 项。
- Xcode iOS 模拟器 BUILD SUCCEEDED；97 个动画资源文件与构建包 SHA-256 一致。浏览器男女视频 readyState=4、8 秒、loop=true，播放及全屏弹层正常。没有重新安装手机，没有改训练计划/记录，没有 commit/push。
- 全库清单刷新：24 项已入包，23 项当前门禁通过，1 项旧版深蹲仍待新门禁审核，1,300 项待制作。旧失败场景/视频在 build/axilla-rebuild/before-delivery/，失败实验留在忽略的 build 目录。

## 2026-10-29 第 002 批继续制作
- 已核实死虫式专项交付，保留其全部改动；当前 24 项 / 48 段已入包。新增 1648、1677、0392、0387、0396、0429、0311、0335 的显式规格和运动适配器。
- 后续扩展握姿和交替方向检查会使第 001 批检查版本失效，将真实重跑旧八个场景和媒体校验，不直接改写哈希绕过门禁。
- 首轮九关键帧检测发现坐姿弯举/前举的大腿碰撞，以及女性 full-can 低位哑铃片接触、侧举接前举中段肩部自交。已按坐姿实际腿部范围调整侧向间距、按人物校准低位和肩部路径，原 2 mm 容差不变，重新烘焙检查。其余动作首轮关键帧通过。
- 已实际查看坐姿交替锤式弯举男女五视角图并验收。坐姿弯举初版虽自动检查通过，但正面肘部张开偏大；进一步收回上臂，低位前臂给哑铃留空间、屈肘后逐渐靠拢，重新制作两个版本后再验收。
- 第二批首轮全帧检查发现男性反握弯举第 57/65 帧的拇指末端与握杆约 4.2 mm 接触；关键帧未覆盖该问题。采用已用于握绳的手指保厚接触修正重新烘焙，不减小检测范围。男女前举/交替前举多视角已实际查看并验收。
- 已实际查看坐姿侧平举和 full-can 男女多视角图：顶部肩高、微曲肘、full-can 拇指朝上及向前约 30° 的抬臂平面可辨认，四版通过视觉验收。
- 男性反握弯举保厚候选导致食指基节新增接触，已拒绝；将改用原握持模式，针对该动作校准 17 mm 表面净空（握杆半径仍 14 mm），重点复查原失败帧及完整循环。检测器与 2 mm 容差不改。
- 多个阶段同时启动导致 Blender 占用过高，已停止尚未完成的坐姿弯举/full-can 渲染进程，保留可续作帧，后续统一以两个 Blender worker 顺序推进。另撤销在重烘焙完成前启动的反握弯举诊断；该次结果不作为验收证据，待源场景保存后重新检查。
- 男性反握弯举最终通过完整 121 帧：增加拇指末两节径向闭合路径 8 mm，原 15.5 mm 表面修正与 14 mm 握杆恢复，双向碰撞/自交、形变、逐指接触、手腕/方向、闭环全部无失败。其余动作默认手指参数保持不变，待该版五视角确认后渲染。
- 新增跨进程生产锁，两项真实多进程测试证明最多两个 Blender worker、同动作/性别阶段互斥。现门禁/交付/并发测试共 25 项通过，另三个错误动作规格反例被正确拒绝。
- 第 002 批完成：8 个精确 ID、16 个可编辑源场景及视频/封面/验收收据。共 2,368 帧全循环检查、2,352 帧正式渲染；所有五视角图实际查看后逐项接受，所有视频完整解码和 alpha 边界检查通过。
- 第一批 1,112 帧使用更新检测器重查，媒体重新校验打包；24 项原目录和全部旧媒体哈希保持不变。批次 002 整批预检后同步，App 累计 32 项 / 64 段；128 个视频/封面哈希正确。
- iOS 模拟器构建 BUILD SUCCEEDED，129 个动画资源文件与源码哈希一致。浏览器测试用 Chrome（内嵌浏览器自动化入口不可用）：男女全部 16 段 readyState=4、无播放错误、5/8 秒时长；男女各一段播放确认，批次筛选显示 8/4/12 项，截图保存 batch-002-preview.jpg。
- 全库清单已刷新：31 项当前检查通过，1 项旧深蹲待新流程复核，1,292 项未实现；仍未完成全库。未安装到手机，未改训练计划/记录，未引入上游媒体，未 commit/push。

## 第 003 批继续制作
- 保留此前 32 项 / 64 段媒体及原目录；新增八种推举的精确规格。新推举检查独立版本绑定，保持原检测文件与既有报告有效，新增动作仍完整检查每一帧。
- 首轮关键帧发现三个版本顶端肩部自交（约 2–4 mm），已给男性站姿与女性中立握平卧保留更自然的上臂外展空间，完整重查。支撑检查最初漏选臀下/近端大腿蒙皮，已补齐实际承重区域，保持间距阈值，随后逐帧复查并目视检查靠垫。

- 首轮 16 版全帧检查通过后，实际五视角审核发现平卧场景头部悬空，女性上背也未贴稳。将这些版本保持待验收，保存四个旧场景；新增平卧头部/上背各自的支撑检查，旧版均被真实拒绝（头部约 53–58 mm、女性上背约 35 mm 间隙）。男女分别校准躯干与颈部姿态，不放宽间距。
- 初次重烘焙暴露角色骨架不含 HeadTop_End，已修正可选末端骨的角度赋值并重新成功生成四版。上斜/坐姿/站姿共 12 版五视角已实际查看、记录，检查器升级后正重新跑本批完整循环；既有批次检查器未变。

- 平卧女性新姿态关键帧通过；男性第一次颈部回调过大导致头部压低、自动配凳后上背悬空，新分区检查再次拒绝。将男性颈部校准至 0.17 rad 后两个动作关键帧均通过，开始全 121 帧复查。检测器与 15 mm 支撑上限不变。
- 四个旧悬空场景、错误中立握规格、错误交替规格共六个真实反例均被拒绝，两项正确规格正例通过；26 项门禁/交付/并发测试通过。非平卧 12 版已完成更新检查器的全帧复验，进入正式渲染。

- 四个平卧最终场景完整 121 帧检查通过，主/正/侧/背/手部图重新查看后接受。实际上背/后脑最大间隙：男性约 2.5/3.27 mm，女性约 7.99/2.5 mm。第 003 批 16 版共 2,224 帧最终检查与全部多视角验收完成，媒体渲染/打包进行中。

- 第 003 批交付完成：8 个动作、16 个源场景与视频/封面/收据，2,208 帧正式渲染，全帧边界和逐段完整解码检查通过。
- 整批预检后同步 App，原 32 项目录及旧 128 个媒体哈希不变。App 累计 40 项 / 80 段；160 个视频/封面与目录摘要相符，iOS 模拟器 BUILD SUCCEEDED，构建包全部 161 个动画资源文件与源码哈希一致。
- Chrome 实际验证男女共 16 段 readyState=4、5/8 秒、loop=true，无播放错误；男性卧推和女性交替上斜推举实际播放通过。批次 003 显示 8 项、全部已交付批次显示 20 项（另有原先 20 项在旧预览目录），截图保存 batch-003-preview.jpg。
- 已生成 batch-003.json 并刷新全库清单：39 项当前检查通过、旧深蹲 1 项待复核、1,284 项未实现。本轮没有安装手机、修改训练计划/记录、引入上游媒体或 commit/push。

## 2026-10-30 第 004 批进行中
- 已编写 8 个精确 ID / 16 男女场景、独立 v4 验收入口，保存原 40 项 / 160 个媒体文件摘要。
- 关键帧发现上斜弯举靠背/大腿碰撞和女性俯身划船大腿碰撞；通过窄靠背与前臂侧向净空修正，未改共享碰撞容差。
- 佐特曼全帧发现辅助前臂 Twist1 在 83/84/182 帧跳转约 174°；保存男女失败源场景/报告到 build/animation-library/batch-004-diagnostics/，改用解剖旋前方向而非越过扭转分支。修正版男女全帧通过，并增加顶部翻腕与底部复位近景检查帧。
- 发布、交付与并发测试合计 27 项通过（23 gate、2 delivery、2 pipeline）；仍须全部场景完成全帧、人工画面验收、正式媒体及 App 构建。

## 2026-10-30 蝴蝶机实物参考修正

实际查看 Life Fitness SS-FLY 官方照片后，重建夹胸与反向飞鸟共用器械：固定双转轴、定长水平摆臂、垂直握把支架、胸/背垫、座椅及配重塔。男女四场景通过每段 121 帧机构、碰撞、形变和握持检查，并查看身体及器械多视角证据后重新渲染。四段正式视频已同步预览及 App，HTTP 内容与本地输出一致。完整计划媒体校验通过（19 项计划动作、34 段新视频、4224 帧）；Xcode 模拟器构建成功，源与构建资源逐文件一致。只更新这四个场景，保留其他动作库制作中的改动；其他器械尚未全部按照片复核。

- 第 004 批交付完成：16 个源场景全帧及五视角验收，2,496 帧正式输出、16 段 H.264 视频与封面，裁切/完整解码/来源收据检查全部通过。
- 0439 文字步骤经 prepare_resources.py 转换为与实际掌心朝前起始版本一致，上游文字及媒体保持不动。
- 同步前重新拍摄目录和文件摘要快照；保留当前 40 项目录和 160 个媒体文件，包括其他并行工作刚更新的 0596/0602 共 8 个文件，没有用本轮初始快照回滚这些更新。最终 App 48 项 / 96 段，iOS 模拟器 BUILD SUCCEEDED，193 个动画资源文件逐个摘要匹配。
- 最终 31 项 gate/delivery/pipeline 测试通过；6 个错误规格、2 个旧旋转跳变场景被拒绝，8 个正确场景对照通过。
- Chrome 实测男女 16 段 readyState=4、5/8 秒、loop=true，男性佐特曼和女性跨体锤式实际播放推进；第 004 批显示 8 项，全体已交付批次显示 28 项。截图 docs/animation-library/batch-004-preview.png，详细账本 batch-004.json。
- 最终清单：47 项通过当前检查、旧深蹲 1 项待复核、1,276 项未制作。未安装手机或 commit/push，训练计划和训练记录未改动；后续按第 005 批继续。

## 2026-10-30 全部现有器械复核进行中
- 盘点到当前已交付 48 个动作 / 96 个男女版本；全部 62 张未修改版本封面已逐张对照查看，覆盖自由重量、平凳、坐凳、训练垫和刚修过的蝴蝶机。
- 对其余 17 个动作 / 34 个版本补齐器械承力与传动，并逐项查看主/侧三帧证据；含原计划 11 项与新增动作库的 6 项靠背训练凳。
- 关键帧碰撞首轮 22 版通过；全帧碰撞、形变、机构和人体不变证明继续运行。未同步未验收候选。
- 过程问题：第一次人体哈希脚本把三角面列表当数组，已转换为 int32 数组；一次合图早于渲染完成，待渲染结束后重新生成完整 34 张证据；新门禁使旧库测试夹具缺少器械报告，已隔离原规格测试并新增四项器械门禁测试，合计 24 项通过。
- 34 版全部通过：4,402 帧机构检查、原有全帧碰撞/形变/动作检查；每帧人物顶点与三角面摘要对比原场景完全一致。新增实际场景反例：导轨偏移 2 cm、脚踏板偏轴 2 cm、配重锁死均被拒绝。
- 新主/侧三姿势图全部实际查看，登记人工审核；旧人体证据仅依据完整网格一致证明复用，新器械证据另附。最终数值检查器重新运行，避免源代码格式调整造成摘要过期。
- 正式渲染启动；首次验收汇总脚本把候选目录误传给 report 参数，改为 root 关键字后全部 34 发布门禁通过。该错误发生在输出前，未替换旧资源。

- 全器械复核交付完成：当前 48 动作 / 96 版本均有照片对照结果；修订其中 17 动作 / 34 版本，4,368 帧正式输出。全部改动媒体完整解码，画面边界通过。旧 124 个视频/封面字节保持不变。
- 预览服务的 34 段视频与本地成品逐项摘要一致，计划及全库页面引用新版本；App 共 48 动作 / 96 段视频，Xcode BUILD SUCCEEDED，193 个构建资源与源码逐文件一致。未安装手机、未改训练计划/记录、未提交或推送。
- 新发布门禁支持包导入和直接脚本两种入口；照片来源摘要同时校验场景内记录，防止更新参考文档后仍误用旧场景。参考照片保存在 ignored build 中，App 仅含原创渲染。

## 第 005 批开始（2026-10-30）
基线 48 项 / 96 段，192 个媒体摘要已保存到 build/animation-library/batch-005-before。当前制作单臂八项，保持旧资产和训练记录。

005 关键姿势初检：14 版本通过；平凳两版本新增纵梁需跟随接触拟合后的垫底高度（初稿固定高度穿入头背）。已修正纵梁定位；仰卧判据纳入人物脊柱自然曲率，以沿凳方向及头/上背实际支撑共同验证。

用户要求核对最新制作流程：2026-10-30 逐项读取 AGENTS.md、animation-pipeline.md 和器械照片流程。发现新握持优先试用保留指厚遗漏，已终止旧候选队列，改用 preserve_thickness 并关闭空闲手的器械接触形态键；全批重新烘焙、检查和生成审核证据。旧 App 成品未变。

保留指厚接入首轮发现空闲手键停用操作早于 Shape Key 创建，烘焙即拒绝退出；已将操作移至修形创建之后，重跑整批。碰撞检测器回归及男女 57 骨绑定/DQ 逆映射/左右修形独立性回归通过。
