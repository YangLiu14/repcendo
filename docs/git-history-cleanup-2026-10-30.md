# 动作资产 Git 历史清理记录

2026-10-30 按用户要求清理本地 Git 历史，运动动作媒体、模型、纹理和审核画面继续保存在本地。没有上传资产，也没有修改 GitHub 远端。

## 清理范围与结果

- 原主线包含 5 个提交。使用独立 bare 副本和 git-filter-repo 2.47.0 重写；作者、提交说明、代码及文字记录保留。
- 提交历史与 Codex 内部快照共识别 832 个私有路径、645 个不同的资产 blob。按路径和 blob ID 同时排除，保留 App 图标和一般界面截图。
- 2 个含资产的内部 tree 引用被删除；清理旧 reflog 可达性。主分支及本地远端跟踪引用指向新历史，其他干净的内部快照保留。
- 清理后逐个检查全部引用及 reflog 可达对象，资产 blob 交集为零。重写后的主线末端 tree 与重写前完全一致，未改变当前版本的代码。
- 切换引用前后，1,974 个本地文件及 Git 索引逐字节一致。其他任务的未提交结果没有被检出、重置或纳入本次提交。
- 不使用立即 prune，以免与其他任务写入 Git 对象发生竞态。不可达旧缓存可能暂留在 `.git/objects`，不参与正常分支 push；推送检查也会拦截重新引用旧历史或资产。

## 私有备份

备份目录位于项目之外：`../repcendo-private-backups/history-cleanup-2026-10-30/`。

| 文件 | 内容 |
| --- | --- |
| `git-directory.tar` | 清理前的完整 `.git`，约 4.49 GiB，含旧引用、对象、reflog 与配置 |
| `local-assets.tar` | 当前模型、视频、纹理、审核证据及相关记录，共 1,797 个文件，约 3.17 GiB；不含可再生的 `.blend1` 自动备份 |
| `local-assets.json` | 每个备份文件的相对路径、大小与 SHA-256 |
| `working-files.tar` / `working-files.json` | 855 个源码及文字文件的快照，包含未提交内容 |
| `working.diff` / `staged.diff` / `index.before` | 原工作差异与索引状态 |
| `archive-checksums.json` | 各 tar 归档的 SHA-256 |
| `initial-refs.json` / `commit-map` / `cutover-result.json` | 清理前引用、新旧提交映射与切换验证记录 |
| `sanitized.git` | 不含私有资产的隔离改写副本 |

归档已完成校验。此前 `build/local-assets/untracked-assets-2026-10-30.tar` 也仍然保留。上述备份与项目在同一台机器，尚未复制到异地存储。

恢复资产时，将 `local-assets.tar` 解压到单独目录核对清单，再按相对路径复制需要的文件。查看旧 Git 数据时，只在隔离目录解包 `git-directory.tar`，不要覆盖当前 `.git` 或给当前仓库新增指向旧历史的备份引用。

## 推送保护与验证

`.git/hooks/pre-push` 调用 Git 目录中保存的独立检查器副本，不依赖当前检出的分支是否含有检查脚本。版本化安装入口为 `Scripts/install_private_asset_guard.py`。

检查覆盖完整祖先历史；不能仅通过删除最新版本中的图片来规避。除目录规则外，还核对已删除资产的 blob ID，因此换路径或扩展名也会被拒绝。推送 Codex 内部引用会被阻止，删除远端引用仍可正常执行。

验证包括：

- 6 项真实临时 Git 仓库回归：资产删除后仍在祖先、内容改名、合法目录、标签及 tree 引用、submodule gitlink、推送/删除引用输入。
- 向本地 bare 测试仓库推送清理后的主线成功。
- 尝试向同一本地测试仓库推送清理前的主线，被实际安装的 hook 拒绝。
- 逐个查询 645 个旧资产 blob，在测试接收端均不存在。

这些验证只使用本机路径，没有向 GitHub 推送。hook 是本机保护，手动禁用 hook 或使用 `--no-verify` 会绕过它；新 clone 需要运行安装命令。

## 远端边界

本次只读查询的 `origin/main` 为 `2d095757ca56dfcc6c8d5d3f386e2968edc606d8`。GitHub 仍保留旧历史，本次没有执行 force push。后续替换远端历史时，需重新核对远端状态，使用指定预期旧提交的 `--force-with-lease`，避免覆盖别人的更新。

工具行为参考：[git-filter-repo 官方说明](https://github.com/newren/git-filter-repo)、[Git pre-push hook](https://git-scm.com/docs/githooks#_pre_push)、[Git 引用事务](https://git-scm.com/docs/git-update-ref)。
