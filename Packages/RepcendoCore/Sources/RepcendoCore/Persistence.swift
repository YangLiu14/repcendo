import Foundation

public struct StateStorage {
    public let fileURL: URL
    public init(fileURL: URL) { self.fileURL = fileURL }

    public func load() throws -> AppState {
        guard FileManager.default.fileExists(atPath: fileURL.path) else { return AppState() }
        let state = try JSONCoding.decoder().decode(AppState.self, from: Data(contentsOf: fileURL))
        guard state.schemaVersion == 1 else {
            throw RepcendoError.message("本地数据来自更新的 App 版本，暂时不能读取。原文件已保留。")
        }
        return state
    }

    public func save(_ state: AppState) throws {
        let data = try JSONCoding.encoder().encode(state)
        try FileManager.default.createDirectory(at: fileURL.deletingLastPathComponent(), withIntermediateDirectories: true)
        try data.write(to: fileURL, options: .atomic)
    }
}

public struct TrainingExport: Codable {
    public let schemaVersion: Int
    public let exportedAt: Date
    public let weightUnit: String
    public let currentPlan: TrainingPlan?
    public let sessions: [WorkoutSession]
    public let inProgress: WorkoutSession?

    public init(state: AppState, now: Date = Date()) {
        schemaVersion = 1; exportedAt = now; weightUnit = "kg"
        currentPlan = state.plan; sessions = state.history; inProgress = state.draft
    }

    public func data() throws -> Data { try JSONCoding.encoder().encode(self) }
}
