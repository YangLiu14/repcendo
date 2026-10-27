import Foundation
import RepcendoCore

guard CommandLine.arguments.count == 3 else {
    fputs("Usage: plan-check <plan.json> <exercises.json>\n", stderr)
    exit(2)
}
do {
    let catalogURL = URL(fileURLWithPath: CommandLine.arguments[2])
    let catalog = try JSONDecoder().decode([Exercise].self, from: Data(contentsOf: catalogURL))
    let plan = try PlanImport.decode(Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])), knownExerciseIDs: Set(catalog.map(\.id)))
    print("有效计划：\(plan.name) · revision \(plan.revision) · \(plan.weeks.count) 周 · \(plan.workoutCount) 次训练")
} catch {
    fputs("校验失败：\(error.localizedDescription)\n", stderr)
    exit(1)
}
