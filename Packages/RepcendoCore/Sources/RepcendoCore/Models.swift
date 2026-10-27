import Foundation

public struct Exercise: Codable, Identifiable, Hashable {
    public var id: String
    public var name: String
    public var localizedName: String?
    public var bodyPart: String
    public var equipment: String
    public var target: String
    public var instructions: [String]
    public var displayName: String { localizedName ?? name }
}

public struct SetTarget: Codable, Hashable {
    public var repsMin: Int
    public var repsMax: Int
    public var weightKg: Double?
    public var rir: Int?
    public var restSeconds: Int

    public init(repsMin: Int = 8, repsMax: Int = 12, weightKg: Double? = nil,
                rir: Int? = nil, restSeconds: Int = 90) {
        self.repsMin = repsMin; self.repsMax = repsMax; self.weightKg = weightKg
        self.rir = rir; self.restSeconds = restSeconds
    }
    public var repsLabel: String { repsMin == repsMax ? "\(repsMin) 次" : "\(repsMin)–\(repsMax) 次" }
}

public struct PlannedExercise: Codable, Identifiable, Hashable {
    public var id: String
    public var exerciseID: String
    public var displayName: String?
    public var notes: String?
    public var sets: [SetTarget]
}

public struct PlannedWorkout: Codable, Identifiable, Hashable {
    public var id: String
    public var name: String
    public var notes: String?
    public var exercises: [PlannedExercise]
    public var setCount: Int { exercises.reduce(0) { $0 + $1.sets.count } }
}

public struct PlanWeek: Codable, Identifiable, Hashable {
    public var week: Int
    public var focus: String
    public var workouts: [PlannedWorkout]
    public var id: Int { week }
}

public struct TrainingPlan: Codable, Identifiable, Hashable {
    public var schemaVersion: Int
    public var id: String
    public var revision: Int
    public var name: String
    public var goal: String
    public var notes: String?
    public var weeks: [PlanWeek]
    public var workoutCount: Int { weeks.reduce(0) { $0 + $1.workouts.count } }
}

public struct LoggedSet: Codable, Identifiable, Hashable {
    public var id = UUID()
    public var target: SetTarget?
    public var weightKg: Double?
    public var reps: Int?
    public var rir: Int?
    public var completed = false

    public init(target: SetTarget? = nil) { self.target = target }
}

public struct LoggedExercise: Codable, Identifiable, Hashable {
    public var id = UUID()
    public var sourceSlotID: String?
    public var exerciseID: String
    public var name: String
    public var sets: [LoggedSet]
    public var notes = ""

    public init(sourceSlotID: String? = nil, exerciseID: String, name: String, sets: [LoggedSet]) {
        self.sourceSlotID = sourceSlotID; self.exerciseID = exerciseID
        self.name = name; self.sets = sets
    }
}

public struct WorkoutSession: Codable, Identifiable, Hashable {
    public var id = UUID()
    public var planID: String
    public var planName: String
    public var planRevision: Int
    public var week: Int
    public var plannedWorkout: PlannedWorkout
    public var startedAt: Date
    public var finishedAt: Date?
    public var exercises: [LoggedExercise]
    public var notes = ""
    public var restEndsAt: Date?

    public init(plan: TrainingPlan, week: Int, workout: PlannedWorkout,
                catalog: [String: Exercise], now: Date = Date()) {
        planID = plan.id; planName = plan.name; planRevision = plan.revision
        self.week = week; plannedWorkout = workout; startedAt = now
        exercises = workout.exercises.map { item in
            LoggedExercise(sourceSlotID: item.id, exerciseID: item.exerciseID,
                name: item.displayName ?? catalog[item.exerciseID]?.displayName ?? item.exerciseID,
                sets: item.sets.map { LoggedSet(target: $0) })
        }
    }
    public var completedSets: Int { exercises.flatMap(\.sets).filter(\.completed).count }
    public var totalSets: Int { exercises.reduce(0) { $0 + $1.sets.count } }
    public var volumeKg: Double {
        exercises.flatMap(\.sets).filter(\.completed).reduce(0) {
            $0 + ($1.weightKg ?? 0) * Double($1.reps ?? 0)
        }
    }
}

public struct AppState: Codable, Equatable {
    public var schemaVersion = 1
    public var plan: TrainingPlan?
    public var history: [WorkoutSession] = []
    public var draft: WorkoutSession?
    public init() {}

    public func isCompleted(planID: String, week: Int, workoutID: String) -> Bool {
        history.contains { $0.planID == planID && $0.week == week && $0.plannedWorkout.id == workoutID }
    }

    public mutating func importPlan(_ incoming: TrainingPlan) throws {
        if let current = plan, current.id == incoming.id, incoming.revision <= current.revision {
            throw RepcendoError.message("这个计划已经是第 \(current.revision) 版。请导入 revision 更大的新版。")
        }
        plan = incoming
    }

    public mutating func finishWorkout(now: Date = Date()) throws {
        guard var session = draft else { throw RepcendoError.message("没有正在进行的训练。") }
        guard session.completedSets > 0 else { throw RepcendoError.message("至少记录并完成一组后，才能结束训练。") }
        for set in session.exercises.flatMap(\.sets) where set.completed {
            try Self.validateActual(set)
        }
        session.finishedAt = now; session.restEndsAt = nil
        history.insert(session, at: 0)
        draft = nil
    }

    public static func validateActual(_ set: LoggedSet) throws {
        guard let weight = set.weightKg, weight.isFinite, (0...2000).contains(weight),
              let reps = set.reps, (1...1000).contains(reps),
              set.rir.map({ (0...10).contains($0) }) ?? true else {
            throw RepcendoError.message("请填写实际重量（0–2000 kg）和次数（1–1000）。自重动作填 0 kg，RIR 可留空或填 0–10。")
        }
    }
}

public enum RepcendoError: LocalizedError {
    case message(String)
    public var errorDescription: String? { if case .message(let value) = self { return value }; return nil }
}

public enum JSONCoding {
    public static func encoder() -> JSONEncoder {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }
    public static func decoder() -> JSONDecoder {
        let decoder = JSONDecoder(); decoder.dateDecodingStrategy = .iso8601
        return decoder
    }
}
