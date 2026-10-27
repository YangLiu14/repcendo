import Foundation
import Observation
import RepcendoCore

@MainActor @Observable
final class AppStore {
    private(set) var state = AppState()
    private(set) var catalog: [Exercise] = []
    private(set) var catalogByID: [String: Exercise] = [:]
    var errorMessage: String?
    var startupError: String?
    var pendingPlan: TrainingPlan?
    var showingWorkout = false
    private let storage: StateStorage

    init() {
        let directory = URL.applicationSupportDirectory.appendingPathComponent("Repcendo", isDirectory: true)
        storage = StateStorage(fileURL: directory.appendingPathComponent("state.json"))
        do {
            guard let url = Bundle.main.url(forResource: "exercises", withExtension: "json") else {
                throw RepcendoError.message("应用的动作库文件缺失，请重新安装完整版本。")
            }
            catalog = try JSONDecoder().decode([Exercise].self, from: Data(contentsOf: url))
            catalogByID = Dictionary(uniqueKeysWithValues: catalog.map { ($0.id, $0) })
            state = try storage.load()
        } catch {
            startupError = "无法读取本地数据：\(error.localizedDescription)\n原始数据已保留，未被重置或覆盖。"
        }
    }

    var dataFileURL: URL { storage.fileURL }

    @discardableResult
    private func commit(_ change: (inout AppState) throws -> Void) -> Bool {
        guard startupError == nil else { return false }
        do {
            var updated = state
            try change(&updated)
            try storage.save(updated)
            state = updated
            return true
        } catch { errorMessage = error.localizedDescription; return false }
    }

    func preview(data: Data) {
        do { pendingPlan = try PlanImport.decode(data, knownExerciseIDs: Set(catalogByID.keys)) }
        catch { errorMessage = error.localizedDescription }
    }

    func preview(url: URL) {
        let accessed = url.startAccessingSecurityScopedResource()
        defer { if accessed { url.stopAccessingSecurityScopedResource() } }
        do {
            let size = try url.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0
            guard size <= PlanImport.maximumBytes else { throw RepcendoError.message("计划文件不能超过 2 MB。") }
            preview(data: try Data(contentsOf: url))
        } catch { errorMessage = "无法打开计划文件：\(error.localizedDescription)" }
    }

    func previewExample() {
        guard let url = Bundle.main.url(forResource: "example-plan", withExtension: "json") else { return }
        preview(url: url)
    }

    func confirmImport() {
        guard let plan = pendingPlan else { return }
        if commit({ try $0.importPlan(plan) }) { pendingPlan = nil }
    }

    func begin(week: Int, workout: PlannedWorkout) {
        guard let plan = state.plan else { return }
        if state.draft != nil { showingWorkout = true; return }
        if commit({ $0.draft = WorkoutSession(plan: plan, week: week, workout: workout, catalog: catalogByID) }) {
            showingWorkout = true
        }
    }

    func editDraft(_ edit: (inout WorkoutSession) -> Void) {
        commit { state in
            guard var draft = state.draft else { return }
            edit(&draft); state.draft = draft
        }
    }

    func editSet(exerciseID: UUID, setID: UUID, edit: (inout LoggedSet) -> Void) {
        editDraft { draft in
            guard let e = draft.exercises.firstIndex(where: { $0.id == exerciseID }),
                  let s = draft.exercises[e].sets.firstIndex(where: { $0.id == setID }) else { return }
            edit(&draft.exercises[e].sets[s])
        }
    }

    func toggleSet(exerciseID: UUID, setID: UUID) {
        commit { state in
            guard var draft = state.draft,
                  let e = draft.exercises.firstIndex(where: { $0.id == exerciseID }),
                  let s = draft.exercises[e].sets.firstIndex(where: { $0.id == setID }) else { return }
            if !draft.exercises[e].sets[s].completed {
                try AppState.validateActual(draft.exercises[e].sets[s])
                let seconds = draft.exercises[e].sets[s].target?.restSeconds ?? 90
                draft.restEndsAt = seconds > 0 ? Date().addingTimeInterval(Double(seconds)) : nil
            }
            draft.exercises[e].sets[s].completed.toggle()
            state.draft = draft
        }
    }

    func addSet(exerciseID: UUID) {
        editDraft { draft in
            guard let i = draft.exercises.firstIndex(where: { $0.id == exerciseID }), draft.exercises[i].sets.count < 30 else { return }
            draft.exercises[i].sets.append(LoggedSet(target: draft.exercises[i].sets.last?.target))
        }
    }

    func removeSet(exerciseID: UUID, setID: UUID) {
        editDraft { draft in
            guard let i = draft.exercises.firstIndex(where: { $0.id == exerciseID }) else { return }
            draft.exercises[i].sets.removeAll { $0.id == setID }
        }
    }

    func chooseExercise(_ exercise: Exercise, replacing id: UUID?) {
        editDraft { draft in
            if let id, let i = draft.exercises.firstIndex(where: { $0.id == id }) {
                // A replacement starts fresh. Already logged work must stay on the original exercise.
                guard !draft.exercises[i].sets.contains(where: \.completed) else { return }
                draft.exercises[i].exerciseID = exercise.id
                draft.exercises[i].name = exercise.displayName
                draft.exercises[i].sets = draft.exercises[i].sets.map { LoggedSet(target: $0.target) }
            } else if draft.exercises.count < 30 {
                draft.exercises.append(LoggedExercise(exerciseID: exercise.id, name: exercise.displayName,
                                                     sets: [LoggedSet()]))
            }
        }
    }

    func removeExercise(id: UUID) { editDraft { $0.exercises.removeAll { $0.id == id } } }
    func finish() { if commit({ try $0.finishWorkout() }) { showingWorkout = false } }
    func discard() { if commit({ $0.draft = nil }) { showingWorkout = false } }

    func previousSets(for exerciseID: String) -> [LoggedSet] {
        for session in state.history {
            let sets = session.exercises.filter { $0.exerciseID == exerciseID }.flatMap(\.sets).filter(\.completed)
            if !sets.isEmpty { return sets }
        }
        return []
    }

    func exerciseName(_ item: PlannedExercise) -> String {
        item.displayName ?? catalogByID[item.exerciseID]?.displayName ?? item.exerciseID
    }
}
