import XCTest
@testable import RepcendoCore

final class RepcendoCoreTests: XCTestCase {
    private var root: URL {
        URL(fileURLWithPath: #filePath).deletingLastPathComponent().appendingPathComponent("../../../../").standardizedFileURL
    }
    private func catalog() throws -> [Exercise] {
        try JSONDecoder().decode([Exercise].self, from: Data(contentsOf: root.appendingPathComponent("Repcendo/Resources/exercises.json")))
    }
    private func plan() throws -> TrainingPlan {
        try PlanImport.decode(Data(contentsOf: root.appendingPathComponent("Examples/first-cycle.json")), knownExerciseIDs: Set(try catalog().map(\.id)))
    }
    private func session(_ plan: TrainingPlan) throws -> WorkoutSession {
        WorkoutSession(plan: plan, week: 1, workout: plan.weeks[0].workouts[0], catalog: Dictionary(uniqueKeysWithValues: try catalog().map { ($0.id, $0) }), now: Date(timeIntervalSince1970: 1_700_000_000))
    }
    private func validSet() -> LoggedSet {
        var set = LoggedSet(target: SetTarget()); set.weightKg = 20; set.reps = 10; set.rir = 2; set.completed = true
        return set
    }

    func testBundledCatalogHasAllUniqueExercisesAndChineseSteps() throws {
        let items = try catalog()
        XCTAssertEqual(items.count, 1324)
        XCTAssertEqual(Set(items.map(\.id)).count, 1324)
        XCTAssertTrue(items.allSatisfy { !$0.instructions.isEmpty })
    }

    func testCatalogClassificationCoversEveryExerciseAndSeparatesGlutesFromThighs() throws {
        let items = try catalog()
        let grouped = Dictionary(grouping: items, by: \.category)
        XCTAssertNil(grouped[.other], "New upstream body parts need an explicit browsing category.")
        XCTAssertEqual(grouped.values.flatMap { $0 }.count, items.count)
        XCTAssertTrue(items.allSatisfy { Exercise.targetNames[$0.target] != nil })
        XCTAssertEqual(grouped[.glutes]?.count, 144)
        XCTAssertEqual(grouped[.thighs]?.count, 83)
        XCTAssertEqual(items.first { $0.id == "0025" }?.category, .chest)
        XCTAssertEqual(items.first { $0.id == "0861" }?.category, .back)
        XCTAssertEqual(items.first { $0.id == "0043" }?.category, .glutes)
        var future = try XCTUnwrap(items.first)
        future.bodyPart = "unknown"; future.target = "unknown"
        XCTAssertEqual(future.category, .other)
        XCTAssertEqual(future.targetDisplayName, "unknown")
    }

    func testExampleHasDifferentWeeklyTargetsAndDeload() throws {
        let plan = try plan()
        XCTAssertEqual(plan.weeks.count, 4)
        XCTAssertNotEqual(plan.weeks[0].workouts[0].exercises[0].sets[0], plan.weeks[1].workouts[0].exercises[0].sets[0])
        XCTAssertLessThan(plan.weeks[3].workouts[0].setCount, plan.weeks[2].workouts[0].setCount)
    }

    func testImportRejectsUnknownExerciseAndMalformedTargets() throws {
        let ids = Set(try catalog().map(\.id))
        var p = try plan(); p.weeks[0].workouts[0].exercises[0].exerciseID = "not-real"
        XCTAssertThrowsError(try PlanImport.validate(p, knownExerciseIDs: ids))
        p = try plan(); p.weeks[0].workouts[0].exercises[0].sets[0].repsMax = 0
        XCTAssertThrowsError(try PlanImport.validate(p, knownExerciseIDs: ids))
        p = try plan(); p.weeks[0].workouts[0].exercises[0].sets[0].weightKg = -.infinity
        XCTAssertThrowsError(try PlanImport.validate(p, knownExerciseIDs: ids))
        p = try plan(); p.weeks[0].workouts[0].exercises[0].sets[0].rir = 11
        XCTAssertThrowsError(try PlanImport.validate(p, knownExerciseIDs: ids))
    }

    func testImportRejectsDuplicateSlotsAndNonsequentialWeeks() throws {
        let ids = Set(try catalog().map(\.id))
        var p = try plan(); p.weeks[0].workouts[0].exercises[1].id = p.weeks[0].workouts[0].exercises[0].id
        XCTAssertThrowsError(try PlanImport.validate(p, knownExerciseIDs: ids))
        p = try plan(); p.weeks[1].week = 1
        XCTAssertThrowsError(try PlanImport.validate(p, knownExerciseIDs: ids))
    }

    func testImportRejectsUnsupportedVersionOversizeAndMissingFields() throws {
        let ids = Set(try catalog().map(\.id))
        var p = try plan(); p.schemaVersion = 2
        XCTAssertThrowsError(try PlanImport.validate(p, knownExerciseIDs: ids))
        XCTAssertThrowsError(try PlanImport.decode(Data(repeating: 32, count: PlanImport.maximumBytes + 1), knownExerciseIDs: ids))
        XCTAssertThrowsError(try PlanImport.decode(Data("{\"schemaVersion\":1}".utf8), knownExerciseIDs: ids)) { error in
            XCTAssertTrue(error.localizedDescription.contains("id"))
        }
    }

    func testMisspelledOptionalWeightIsRejectedInsteadOfSilentlyDropped() throws {
        let source = try String(contentsOf: root.appendingPathComponent("Examples/first-cycle.json"), encoding: .utf8)
        let malformed = Data(source.replacingOccurrences(of: "weightKg", with: "weightKG").utf8)
        XCTAssertThrowsError(try PlanImport.decode(malformed, knownExerciseIDs: Set(try catalog().map(\.id)))) { error in
            XCTAssertTrue(error.localizedDescription.contains("weightKG"))
        }
    }

    func testPlanUpdatePreservesHistoryDraftAndCompletionAcrossRevisions() throws {
        let original = try plan()
        var state = AppState(); try state.importPlan(original)
        var finished = try session(original)
        finished.exercises[0].sets[0] = validSet(); finished.finishedAt = Date(timeIntervalSince1970: 1_700_003_600)
        state.history = [finished]; state.draft = try session(original)
        let oldDraft = state.draft
        var updated = original; updated.revision = 2
        updated.weeks[0].workouts[0].exercises[0].sets[0].weightKg = 80
        try state.importPlan(updated)
        XCTAssertEqual(state.history, [finished])
        XCTAssertEqual(state.draft, oldDraft)
        XCTAssertEqual(state.plan?.revision, 2)
        XCTAssertNil(state.draft?.plannedWorkout.exercises[0].sets[0].weightKg)
        XCTAssertTrue(state.isCompleted(planID: original.id, week: 1, workoutID: "a"))
        XCTAssertThrowsError(try state.importPlan(original))
        XCTAssertThrowsError(try state.importPlan(updated))
        XCTAssertEqual(state.plan?.revision, 2)
    }

    func testNewCycleDoesNotInheritOldCompletion() throws {
        var p = try plan(); var state = AppState()
        var old = try session(p); old.finishedAt = Date()
        state.history = [old]
        p.id = "next-cycle"; try state.importPlan(p)
        XCTAssertFalse(state.isCompleted(planID: p.id, week: 1, workoutID: "a"))
        XCTAssertEqual(state.history.count, 1)
    }

    func testFinishRecordsOnlyCompletedWorkAndKeepsOriginalTargets() throws {
        let p = try plan(); var state = AppState(); state.draft = try session(p)
        state.draft?.exercises[0].sets[0] = validSet()
        state.draft?.exercises[0].sets[1].weightKg = 100
        state.draft?.exercises[0].sets[1].reps = 100
        let end = Date(timeIntervalSince1970: 1_700_003_600)
        try state.finishWorkout(now: end)
        XCTAssertNil(state.draft)
        XCTAssertEqual(state.history[0].finishedAt, end)
        XCTAssertEqual(state.history[0].completedSets, 1)
        XCTAssertEqual(state.history[0].volumeKg, 200)
        XCTAssertEqual(state.history[0].plannedWorkout, p.weeks[0].workouts[0])
    }

    func testFinishRejectsEmptyAndInvalidActualsWithoutDiscardingDraft() throws {
        var state = AppState(); state.draft = try session(plan())
        XCTAssertThrowsError(try state.finishWorkout())
        state.draft?.exercises[0].sets[0] = validSet()
        state.draft?.exercises[0].sets[0].weightKg = nil
        XCTAssertThrowsError(try state.finishWorkout())
        XCTAssertNotNil(state.draft); XCTAssertTrue(state.history.isEmpty)
        var bodyweight = validSet(); bodyweight.weightKg = 0
        XCTAssertNoThrow(try AppState.validateActual(bodyweight))
    }

    func testDiskRoundTripRestoresDraftAndTimer() throws {
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: folder) }
        let storage = StateStorage(fileURL: folder.appendingPathComponent("state.json"))
        XCTAssertEqual(try storage.load(), AppState())
        var state = AppState(); state.plan = try plan(); state.draft = try session(plan())
        state.draft?.exercises[0].sets[0] = validSet()
        state.draft?.restEndsAt = Date(timeIntervalSince1970: 1_700_000_090)
        try storage.save(state)
        XCTAssertEqual(try storage.load(), state)
        state.draft?.notes = "今天状态不错"
        try storage.save(state)
        XCTAssertEqual(try storage.load().draft?.notes, "今天状态不错")
    }

    func testCorruptOrFutureStorageFailsWithoutOverwritingFile() throws {
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: folder) }
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let url = folder.appendingPathComponent("state.json")
        let bytes = Data("corrupted".utf8); try bytes.write(to: url)
        XCTAssertThrowsError(try StateStorage(fileURL: url).load())
        XCTAssertEqual(try Data(contentsOf: url), bytes)
        var state = AppState(); state.schemaVersion = 2
        try StateStorage(fileURL: url).save(state)
        XCTAssertThrowsError(try StateStorage(fileURL: url).load())
    }

    func testExportIncludesTargetsActualsNotesAndDraft() throws {
        var state = AppState(); state.plan = try plan(); state.draft = try session(plan())
        state.draft?.exercises[0].sets[0] = validSet(); state.draft?.notes = "临时调整"
        let exported = TrainingExport(state: state, now: Date(timeIntervalSince1970: 1_700_003_600))
        let decoded = try JSONCoding.decoder().decode(TrainingExport.self, from: exported.data())
        XCTAssertEqual(decoded.weightUnit, "kg")
        XCTAssertEqual(decoded.currentPlan, state.plan)
        XCTAssertEqual(decoded.inProgress, state.draft)
        XCTAssertEqual(decoded.inProgress?.notes, "临时调整")
        XCTAssertEqual(decoded.inProgress?.exercises[0].sets[0].reps, 10)
    }
}
