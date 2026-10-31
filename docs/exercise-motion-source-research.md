# 健身动作真人参考与动作数据来源调研

核查日期：2026-10-30。用途：为 Repcendo 的 1,324 个动作、男女两个角色版本建立动作参考，而不是采购现成动画替换原创制作。本次没有购买、注册、批量下载或导入第三方媒体。

## 结论

可以建立参考体系，但本次没有找到“覆盖项目全部 1,324 个精确变体、含男女多视角真人示范、可直接用于商业 AI 辅助动画制作”的现成开放数据集。建议把来源分为：真人示范（辨认真实姿态和运动路径）、教练说明（确认执行要点）、三维动作数据（辅助测量与重定向）。三者不能互相替代。另一套 3D 动画不能单独证明动作符合人体运动方式。

**优先评估 MuscleWiki 的真人多视角覆盖，使用 ACE / PureGym 的第一方教练资料交叉核对；需要本地逐帧图片、姿态提取或 AI 辅助生产时，先落实对应授权。** 对缺失变体，明确标记未覆盖，采用获授权的真人补拍，而不是从相似名称推算动作。男女输出仍分别验收；参考站提供男女选择不代表每个具体动作都有两个性别和全部视角。

## 来源比较

| 来源 | 已核实能提供什么 | 对本项目的用途与边界 |
| --- | --- | --- |
| [MuscleWiki](https://musclewiki.com/exercise/dumbbell-upright-row) / [官方 API](https://api.musclewiki.com/) | 官网公布 1,900+ 动作、7,700+ 视频；[文档](https://api.musclewiki.com/documentation)支持按器械、性别、肌群检索，视频含角度选项。具体直立划船页有正面/侧面媒体入口。 | 最值得做精确覆盖评估的真人参考候选。数量是供应商公布的总量，不是与本库的匹配结果；尚未用付费 API 拉取全库核对。普通 API 授权不能作为本地图片仓库授权。 |
| [ACE Exercise Library](https://www.acefitness.org/resources/everyone/exercise-library/) | 第一方动作说明和照片，按身体部位、器械、难度浏览。 | 适合基础动作的姿态与执行说明交叉核对。本次未确认覆盖全部细分变体，也未找到完整可商用批量媒体 API；[条款](https://www.acefitness.org/legal/terms-of-use/)没有授予商业复制使用权限。 |
| [PureGym Exercise Guides](https://www.puregym.com/exercises/arms-and-shoulders/upright-rows/dumbbell-upright-row/) | 找到与问题动画精确对应的双哑铃直立划船页面，含示范图片、嵌入视频、步骤与动作变体链接。 | 当前问题的优先真人核对入口。不能仅凭页面公开就认定允许下载、重发或自动抽帧；本次未确认对应生产用途的媒体授权。 |
| [ExRx](https://exrx.net/WeightExercises/DeltoidLateral/DBUprightRow) | 找到直立划船的具体动作入口，但本次正文访问受 robots 限制；不能声称已观看其示范。 | 保留作人工专业检索/授权洽谈候选。本次检索到的[官方条款](https://exrx.net/Notes/Legal)允许保存页面链接，限制抓取、复制和再发布，并指向内容授权；不要作为自动抓取源。条款正文直开也受限，需在实际采用前复核。 |
| [wger](https://github.com/wger-project/wger) | 开源动作库和 REST API；官方明确动作数据按各条目的 Creative Commons 许可管理。 | 可补充结构化术语与逐项许可明确的图片/视频。代码 AGPL 与素材许可不同；不能假定每条都有真人视频、完整循环、多视角或同等质量。 |
| [Fit3D](https://fit3d.imar.ro/fit3d) | 611 次记录、4 视角、50 fps、三维骨架及 GHUM / SMPL-X 参数；当前详情页列 47 类动作，而旧摘要写 37 类。 | 可研究关节轨迹和对齐方法，覆盖远小于 1,324。数据包含教练与学员，不能把全部序列当作标准动作。[下载需账号](https://fit3d.imar.ro/download)；[默认许可限非商业研究/教育/艺术](https://fit3d.imar.ro/legal)，商业用途需单独授权。 |
| [FLAG3D](https://andytang15.github.io/FLAG3D/) | 60 类动作、180K 序列，包含动作捕捉、渲染视频和自然场景真人视频。 | 不是 180K 个不同动作，也不是全部真人拍摄。[官方许可](https://andytang15.github.io/FLAG3D/License_FLAG3D.pdf)限科研、需机构签署申请，并明确禁止包括测试商业系统在内的商业用途；不能直接用于当前产品生产。 |
| [MM-Fit](https://mmfit.github.io/) | 10 类动作、800+ 分钟，多传感器与 RGB-D、二维/三维姿态估计。 | 可研究时间连续性和重复分段，姿态估计不能当 Vicon 动捕真值；覆盖很窄。视频发布版本 [Zenodo 7672767](https://zenodo.org/records/7672767) 的[官方 API 元数据](https://zenodo.org/api/records/7672767)已核实 `metadata.license.id = cc-by-4.0`，是可进一步试验的开放来源；须按 CC BY 4.0 署名并标明修改，不能把该视频许可自动套给其他下载包或人体模型，也不能把学员动作直接当正确模板。 |

## ExerciseDB 与现有子模块不能混为一个许可

1. **现有 `hasaneyldrm/exercises-dataset`**：本地固定版本 `7455efae41b330c265e7cd4b78dfa848e7ce5ebd`，1,324 项。其 [LICENSE](https://github.com/hasaneyldrm/exercises-dataset/blob/main/LICENSE) 及本地 `NOTICE.md` 明确：MIT 覆盖代码、结构、说明文字，`images/` 与 `videos/` 属于 Gym visual，克隆仓库不授予媒体使用权。
2. **Gym visual**：[直立划船商品页](https://gymvisual.com/animated-gifs/1938-dumbbell-upright-row.html)销售动画 GIF，不能当成真人动作证据。[使用条款 §6.2](https://gymvisual.com/content/3-terms-and-conditions-of-use)明确限制以其媒体为基础用 AI 工具生成图片、动画和视频；普通商业媒体购买不等于当前制作流程获得授权。未取得另行书面授权前，不把现有 GIF 导入 AI 制作参考集，也不放进 App。
3. **ExerciseDB.io / EDB Exercise Intelligence**：[FAQ](https://exercisedb.io/faq)公布 1,394 项，是离线数据与 GIF 包，并非该站销售的订阅 API。[条款](https://exercisedb.io/terms)允许已购包按条件用于产品，不允许把原始库/媒体再打包为独立库或竞品。其条款不能替其他供应商或当前子模块授权，也没有据此确认真人来源或 AI 制作许可。
4. **ExerciseDB.dev / AscendAPI**：[当前入口](https://exercisedb.dev/)已标为 AscendAPI；[V2 文档](https://docs.ascendapi.com/products/edb-v2/overview)公布 11,000+ 动作、15,000+ 视频、20,000+ 图片，需 RapidAPI 订阅。媒体总量与供应商的“专家验证”宣传不等于本次已核验全库或真人覆盖。[缓存文档](https://docs.ascendapi.com/guides/caching)按套餐限制存储，媒体 URL 定期变化，持久存储/批量下载需另谈。旧 Notion 条款与新文档的缓存说法不同，购买前必须取得适用版本的协议。

## 双臂哑铃直立划船：本次找到的具体参考

- [NCSF — Contraindicated Exercises](https://www.ncsf.org/pdf/ceu/contraindicated_exercises.pdf)：PDF 物理第 6 页、印刷页码第 4 页的 High Angle Upright Row 已实际查看 Incorrect / Correct 真人对照（左图为高拉杠铃，右图为双哑铃，不是同器械的严格对照实验），给出哑铃上臂外展至 90° 的修正示例。可作为本项目选择较保守示范幅度的依据；这是该资料的动作建议，不是“人类肩关节绝不可能超过 90°”的解剖定律。
- [PureGym — Dumbbell Upright Row](https://www.puregym.com/exercises/arms-and-shoulders/upright-rows/dumbbell-upright-row/)：精确匹配站姿、双哑铃、双臂动作；页面描述肘向外上提、负重靠近身体、受控回落，并说明高度依肩部活动能力和舒适度调整。适合核对起点、上提、最高点和回程；不能把网页说明反推成所有人的统一关节角度。
- [MuscleWiki — Dumbbell Upright Row](https://musclewiki.com/exercise/dumbbell-upright-row/)：页面提供正面/侧面媒体入口和性别选择，但正文有“每只手握两个哑铃”的疑似表述错误，高点说明也与 PureGym 的表述不同。这正说明来源需要实际看图/视频和交叉核对，不能只把动作文字转成骨骼角度。
- 单臂版本必须另外核对躯干稳定、空闲手与负重侧路径，不能把双臂参考直接认定为单臂已验收。具体媒体未完整播放之前，只能记为“已找到参考入口”，不能登记“参考姿态已验收”。

截图显示的是需要重新检查的肩肘造型与运动协调问题。仅凭“肘高过肩”不足以认定解剖上不可能：不同示范的幅度并不一致，PureGym 也允许按个体活动度调整。实际修复需要检查上臂旋转、肩带联动、肘屈伸平面和皮肤形变，不能只降低手的位置或换机位遮挡。

## 建议落到制作流程的字段与检查

以下是项目建议，不是来源网站对本项目的认证：

1. 每个动作记录 `exerciseId`、器械、站/坐/卧姿、握法、单双侧、支撑点；来源必须匹配这些维度，不能只靠名称相似。
2. 记录第一方页面 URL、访问日期、真人/动画标记、可用视角、时间点或图序、来源许可和允许用途。保留 `reference_found` 与 `reference_reviewed` 的区别。
3. 起始、过渡、峰值、回程逐项对照；肩带/上臂旋转、肘屈伸平面、前臂旋转、腕线、髋膝踝、躯干稳定和接触点都在核对范围。单张峰值图不能验收一个循环。
4. 保留逐帧穿插、长度、速度连续性检查，并新增源于实际参考的动作约束；避免凭空设一套通用角度阈值。碰撞通过不能替代人体姿态验收。
5. 输出男女各自的主视图与必要补充视图对照结论；不以同一骨骼程序替代两份视觉验收。缺真人证据或许可不清的条目进入待补参考状态，不计入通过。
6. 本地关键帧库优先采用逐项许可允许的媒体或自行拍摄并取得表演者授权；商业 API 的播放权、离线缓存权、姿态数据提取权、AI 辅助制作权和最终素材发布权分别确认。

## 本次核查的实际范围

完成第一方产品页、动作页、官方文档与条款检索、本地固定子模块的许可核对，以及 NCSF 指定页真人对照图的实际查看。NCSF PDF 仅作为本地研究缓存放在忽略的 build 目录；PureGym 图片直取返回 403，未绕过限制，未完整播放其视频。没有完成 1,324 项逐一映射，没有购买或测试付费 API，没有证明任何来源能一站式覆盖全部男女变体，也没有把引用入口标成已经完成逐帧视觉验收。本报告是来源选择依据，不是当前问题动画的修复或重新验收记录。
