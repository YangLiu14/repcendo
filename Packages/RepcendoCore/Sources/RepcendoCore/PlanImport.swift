import Foundation

public enum PlanImport {
    public static let maximumBytes = 2_000_000

    public static func decode(_ data: Data, knownExerciseIDs: Set<String>) throws -> TrainingPlan {
        guard data.count <= maximumBytes else { throw RepcendoError.message("计划文件不能超过 2 MB。") }
        try checkFields(data)
        let plan: TrainingPlan
        do { plan = try JSONCoding.decoder().decode(TrainingPlan.self, from: data) }
        catch let error as DecodingError { throw RepcendoError.message(describe(error)) }
        try validate(plan, knownExerciseIDs: knownExerciseIDs)
        return plan
    }

    public static func validate(_ plan: TrainingPlan, knownExerciseIDs: Set<String>) throws {
        try require(plan.schemaVersion == 1, "目前只支持 schemaVersion: 1。")
        try identifier(plan.id, "计划 id")
        try require((1...100000).contains(plan.revision), "revision 必须为正整数，最大 100000。")
        try title(plan.name, "计划名称")
        try require(plan.goal.count <= 2000 && (plan.notes?.count ?? 0) <= 10000, "计划说明过长。")
        try require((1...52).contains(plan.weeks.count), "计划应包含 1–52 周。")
        try require(plan.weeks.map(\.week) == Array(1...plan.weeks.count), "weeks 必须按 week 从 1 开始连续排列。")
        for week in plan.weeks {
            let prefix = "第 \(week.week) 周"
            try require(week.focus.count <= 2000, "\(prefix)的训练重点过长。")
            try require((1...14).contains(week.workouts.count), "\(prefix)应包含 1–14 次训练。")
            try unique(week.workouts.map(\.id), "\(prefix)训练 id")
            for workout in week.workouts {
                try identifier(workout.id, "训练 id"); try title(workout.name, "训练名称")
                try require((workout.notes?.count ?? 0) <= 10000, "训练说明过长。")
                try require((1...30).contains(workout.exercises.count), "\(workout.name)应包含 1–30 个动作。")
                try unique(workout.exercises.map(\.id), "\(workout.name)动作栏位 id")
                for item in workout.exercises {
                    try identifier(item.id, "动作栏位 id")
                    try require(knownExerciseIDs.contains(item.exerciseID), "动作 ID \(item.exerciseID) 不在动作库中，请使用目录中的真实 ID。")
                    if let name = item.displayName { try title(name, "动作显示名称") }
                    try require((item.notes?.count ?? 0) <= 5000, "动作说明过长。")
                    try require((1...30).contains(item.sets.count), "每个动作应包含 1–30 组。")
                    for target in item.sets {
                        try require((1...1000).contains(target.repsMin) && target.repsMax >= target.repsMin && target.repsMax <= 1000,
                                    "\(item.exerciseID)：次数范围必须在 1–1000 内，且上限不能小于下限。")
                        try require(target.weightKg.map { $0.isFinite && (0...2000).contains($0) } ?? true, "重量应为 0–2000 kg 或 null。")
                        try require(target.rir.map { (0...10).contains($0) } ?? true, "RIR 应为 0–10 或 null。")
                        try require((0...1800).contains(target.restSeconds), "组间休息应为 0–1800 秒。")
                    }
                }
            }
        }
    }

    private static func require(_ condition: Bool, _ message: String) throws {
        if !condition { throw RepcendoError.message(message) }
    }
    private static func checkFields(_ data: Data) throws {
        guard let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return }
        func check(_ object: [String: Any], _ fields: Set<String>, _ path: String) throws {
            if let unexpected = Set(object.keys).subtracting(fields).sorted().first {
                throw RepcendoError.message("未知字段 \(path).\(unexpected)，请检查拼写并对照计划格式。")
            }
        }
        try check(root, ["schemaVersion", "id", "revision", "name", "goal", "notes", "weeks"], "plan")
        for week in root["weeks"] as? [[String: Any]] ?? [] {
            try check(week, ["week", "focus", "workouts"], "week")
            for workout in week["workouts"] as? [[String: Any]] ?? [] {
                try check(workout, ["id", "name", "notes", "exercises"], "workout")
                for exercise in workout["exercises"] as? [[String: Any]] ?? [] {
                    try check(exercise, ["id", "exerciseID", "displayName", "notes", "sets"], "exercise")
                    for set in exercise["sets"] as? [[String: Any]] ?? [] {
                        try check(set, ["repsMin", "repsMax", "weightKg", "rir", "restSeconds"], "set")
                    }
                }
            }
        }
    }
    private static func identifier(_ value: String, _ label: String) throws {
        try require(value.range(of: "^[A-Za-z0-9_-]{1,80}$", options: .regularExpression) != nil,
                    "\(label)只允许 1–80 个英文字母、数字、下划线或连字符。")
    }
    private static func title(_ value: String, _ label: String) throws {
        try require(!value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && value.count <= 200,
                    "\(label)不能为空，最长 200 字。")
    }
    private static func unique(_ ids: [String], _ label: String) throws {
        try require(Set(ids).count == ids.count, "\(label)不能重复。")
    }
    private static func describe(_ error: DecodingError) -> String {
        switch error {
        case .keyNotFound(let key, let context):
            return "计划缺少字段：\((context.codingPath.map(\.stringValue) + [key.stringValue]).joined(separator: "."))。"
        case .typeMismatch(_, let context), .valueNotFound(_, let context):
            return "字段类型不正确：\(context.codingPath.map(\.stringValue).joined(separator: "."))。请对照示例计划。"
        default: return "无法读取 JSON，请检查文件格式与示例计划是否一致。"
        }
    }
}
