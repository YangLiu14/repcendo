# Repcendo · 渐强

给自己用的 iOS 训练记录 App。Codex 制定和调整周期计划，App 负责执行、记录和反馈。

SwiftUI · iOS 17+ · 离线存储 · 无账号、无第三方运行时依赖。

## 运行

1. 用 Xcode 打开 `Repcendo.xcodeproj`。
2. 选择 `Repcendo` scheme 和 iPhone 模拟器，点击 Run。
3. 首次启动点「先体验示例计划」，预览并确认导入。

真机安装：在 Signing & Capabilities 中选择自己的开发团队，并使用可用的 Bundle Identifier；选择连接的 iPhone 运行。首次安装可能需要在手机上开启开发者模式。工程不包含任何个人签名信息。

## 已实现

- 导入 JSON 计划，先校验和预览；支持从「文件」App 打开。拒绝不存在的动作、错误字段和旧版本。
- 周期内每周可设置不同目标。训练顺序自由选择，已完成安排自动标记。
- 实际重量、次数、RIR 与计划目标分别保存；显示上次同动作的表现。
- 完成一组后开始休息计时；按截止时间计算，切到后台再回来仍准确。第一版没有后台通知。
- 随时增减组数、添加/删除动作、替换尚未完成的动作。已有完成组的动作可保留，再添加替代动作。
- 自动保存训练草稿；退出、重启后继续。支持部分完成并保留未完成组。
- 查看训练历史、原计划快照，以及每个动作的重量趋势和逐组记录。
- 导出当前计划、完整历史和草稿给 Codex。更新计划保留历史和正在执行的训练。
- 全部 1,324 个动作的文字数据、中文步骤、器械/肌群筛选。常用示例动作附中文名称，其余保留上游英文名；可搜索英文、器械、肌群或 ID。

重量统一使用 kg，自重动作填 0；哑铃保持一致的单只计重方式。第一版用于次数型训练，不包含计时/距离型动作记录。

## 和 Codex 协作

生成或更新计划时，让 Codex 读取 [计划生成说明](docs/codex-plans.md)。完整例子在 [first-cycle.json](Examples/first-cycle.json)，机器可读字段约束在 [plan.schema.json](docs/plan.schema.json)。示例只演示格式，不是个人训练建议。

```sh
swift run --package-path Packages/RepcendoCore plan-check Examples/first-cycle.json Repcendo/Resources/exercises.json
```

训练完成后在「记录 → 导出给 Codex」保存反馈 JSON，再交给 Codex。反馈 JSON 与计划 JSON 用途不同，反馈不作为计划导入。数据存于本机 Application Support 下的 `Repcendo/state.json`；读写失败会报错而不会重置数据。反馈导出用于分析和留存，目前不提供备份恢复或跨设备同步，删除 App 会丢失本地记录。

## 开发与验证

```sh
swift test --package-path Packages/RepcendoCore
xcodebuild -project Repcendo.xcodeproj -scheme Repcendo -sdk iphonesimulator -configuration Debug -derivedDataPath build CODE_SIGNING_ALLOWED=NO build
```

UI 测试覆盖导入、记录、重启恢复、结束、历史、导出入口和动作检索。使用新建的专用模拟器，不会清空用户数据：

```sh
bash Scripts/test_ios.sh
```

脚本默认使用本机已安装的 iOS 26.3 / iPhone 17 Pro，结束后删除自己创建的测试设备。可传入 runtime 和 device type 两个参数；结果与截图留在 `build/*.xcresult`。

深色和减少动态效果检查可使用：

```sh
REPCENDO_QA_APPEARANCE=dark REPCENDO_QA_REDUCE_MOTION=1 bash Scripts/test_ios.sh
```

实际运行截图见 [计划首页](docs/screenshots/02-plan.png)、[训练记录](docs/screenshots/03-workout.png) 和 [历史页面](docs/screenshots/04-history.png)。截图使用明确标注的示例计划与测试数据。

本次验证：13 项核心测试通过；iPhone 17 Pro 与深色 iPad mini 的两项 UI 测试及 runner 成功；375pt iPhone SE 的两项 UI 用例通过，但 Xcode 收尾停滞后需终止 runner。已检查最大动态字体与横屏截图。运行环境为 Xcode 27.1 / iOS 26.3；iOS 17 为编译最低版本，尚未进行 iOS 17 运行测试或真机验证。深色预览见 [iPad 训练页](docs/screenshots/11-ipad-dark-workout.png)。

`Packages/RepcendoCore` 保存模型、计划校验、原子文件存储和反馈格式。`Repcendo` 是 App。需要新增源文件后运行 `python3 Scripts/generate_project.py` 更新工程引用；工程已提交，无需安装 XcodeGen。

## Exercise dataset

[exercises-dataset](https://github.com/hasaneyldrm/exercises-dataset) is included as a Git submodule at `third_party/exercises-dataset`.

After cloning this repository, initialize the pinned dataset version:

```sh
git submodule update --init --recursive
```

Exercise data is in `third_party/exercises-dataset/data/exercises.json`. See the submodule's `LICENSE` and `NOTICE.md` for data and media usage terms.

应用只打包 MIT 授权的文字数据；图片/GIF 的独立授权尚未取得，因此不打包媒体。原许可证在 App「动作详情 → 开源许可」可查看。

更新 submodule 后，重新生成精简数据与资源：

```sh
python3 Scripts/prepare_resources.py
python3 Scripts/generate_project.py
```

## 原创动作动画

已制作希腊雕塑风格的深蹲、卧推、坐姿划船，男女各一版，包含五指骨架、肌群材质和可编辑场景。目前为独立资产，尚未接入 App。

- [制作流水线与新增动作步骤](docs/animation-pipeline.md)
- [六段动作样片与验证说明](docs/animation-samples-v2/README.md)
- [可复用男女骨架资产](docs/character-assets/hand-rig-v1/README.md)

使用安装了 Pillow 的 Python 和 PATH 中的 Blender / ffmpeg / ffprobe：

```sh
python3 Scripts/animation_samples/pipeline.py --mode full
```
