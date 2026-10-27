# 为 Repcendo 生成与调整计划

面向为用户生成计划的 Codex。输出一个 UTF-8 JSON 文件，用户可通过 iPhone「文件」或 App 的「导入我的计划」打开。

## 生成步骤

1. 先确认用户本轮目标、可训练时间、可用器械，以及需要避开的动作；已有明确上下文时直接沿用。
2. 读取 `Examples/first-cycle.json` 了解完整结构，读取 `docs/plan.schema.json` 获取字段约束。
3. 从 `Repcendo/Resources/exercises.json` 查找动作的真实 `id`。ID 是保留前导零的字符串；可按英文名称、肌群、器械检索。用 `displayName` 提供自然的中文名称。
4. 逐周明确目标；每组显式填写次数范围、重量目标（未知时 `null`）、RIR（可选）和休息秒数。第一版只记录次数型训练，重量单位 kg；自重的外加负重为 0 kg。
5. 调整已有周期时，沿用计划 `id`，提高 `revision`，保留相同训练的 `week` 和 workout `id`。每次导入都是完整替换当前周期，输出完整计划，而非 JSON patch。新的周期使用新的计划 `id`，从 week 1 开始。
6. 将文件保存到 `Plans/` 或用户指定目录，运行下面的校验命令。只有校验通过后才交付链接，并简述这一版变化。

```sh
swift run --package-path Packages/RepcendoCore plan-check Plans/my-plan.json Repcendo/Resources/exercises.json
```

## 使用反馈

反馈 JSON 由 App 的「记录 → 导出给 Codex」生成。读取 `currentPlan` 和 `sessions`；`inProgress` 是未完成草稿，单独考虑。

- 每次训练的 `plannedWorkout` 是不可变的原计划快照；`exercises` 是实际选择的动作和记录。
- 只将 `completed: true` 的组计入实际完成训练；空值表示没有记录，不代表 0。
- `weightKg` 是用户填写的重量，哑铃按用户约定的单只重量记录；不会自动推断双手重量。
- `rir` 表示完成一组后估计还能做的次数；null 表示未记录。
- 结合实际次数、重量、RIR、未完成组与 `notes` 调整目标。目标与事实分别陈述；资料不足时说明缺口。
- `finishedAt - startedAt` 含中途暂停，不等于实际运动时长。
- 更新计划不会改写历史或正在执行的草稿。完成状态由 `(planID, week, workoutID)` 决定，和 revision 无关；保持 ID 稳定，避免把已完成安排重新标成待练。

## 交付检查

校验器成功退出；动作 ID 均来自目录；周期 id/revision 符合新建或更新语义；文件中有完整周安排。示例计划只演示格式，不能当作用户的个性化方案。
