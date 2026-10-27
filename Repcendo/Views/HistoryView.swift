import SwiftUI
import Charts
import RepcendoCore

struct HistoryView: View {
    @Environment(AppStore.self) private var store
    @State private var exporting = false
    @State private var document = JSONDocument(data: Data())
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                VStack(alignment: .leading, spacing: 8) {
                    Eyebrow(text: "PROGRESS / 训练积累")
                    Text("把进步，留有记录。").font(.largeTitle.bold())
                }.padding(.top, 16)
                if store.state.history.isEmpty {
                    Card {
                        Image(systemName: "chart.xyaxis.line").font(.largeTitle).foregroundStyle(Theme.accent).accessibilityHidden(true)
                        Text("你的第一笔积累").font(.title2.bold())
                        Text("完成训练后，重量、次数和计划执行情况会出现在这里。")
                            .foregroundStyle(Theme.secondary)
                    }
                } else {
                    Card {
                        HStack {
                            Metric(value: "\(store.state.history.count)", label: "完成训练")
                            Metric(value: "\(store.state.history.reduce(0) { $0 + $1.completedSets })", label: "完成组数")
                        }
                    }
                    let ids = Set(store.state.history.flatMap(\.exercises).filter { $0.sets.contains(where: \.completed) }.map(\.exerciseID)).sorted()
                    Card {
                        Text("动作表现").font(.headline)
                        Text("查看相同动作每次训练的实际记录。").font(.caption).foregroundStyle(Theme.secondary)
                        ForEach(ids, id: \.self) { id in
                            NavigationLink(value: ProgressRoute(exerciseID: id)) {
                                HStack {
                                    Text(store.catalogByID[id]?.displayName ?? id).font(.subheadline)
                                    Spacer()
                                    Image(systemName: "chevron.right").font(.caption).accessibilityHidden(true)
                                }.frame(minHeight: 44)
                            }
                        }
                    }
                    Text("训练历史").font(.title3.bold())
                    ForEach(store.state.history) { session in
                        NavigationLink(value: session) {
                            Card {
                                HStack {
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text(session.plannedWorkout.name).font(.headline).foregroundStyle(.primary)
                                        Text(session.startedAt, format: .dateTime.month().day().hour().minute())
                                            .font(.caption).foregroundStyle(Theme.secondary)
                                    }
                                    Spacer()
                                    VStack(alignment: .trailing, spacing: 8) {
                                        Text("\(session.completedSets) 组").font(.headline).foregroundStyle(Theme.accent)
                                        Text("训练量 \(weightText(session.volumeKg)) kg").font(.caption).foregroundStyle(Theme.secondary)
                                    }
                                }
                            }
                        }.buttonStyle(.plain)
                    }
                }
                Card {
                    Eyebrow(text: "交给下一阶段的自己")
                    Text("让下一份计划，更懂你。").font(.title3.bold())
                    Text("导出当前计划、实际记录和训练备注，把文件交给 Codex，作为下一轮调整的依据。")
                        .font(.subheadline).foregroundStyle(Theme.secondary)
                    PrimaryButton(title: "导出给 Codex", icon: "square.and.arrow.up") {
                        do {
                            document = JSONDocument(data: try TrainingExport(state: store.state).data()); exporting = true
                        } catch { store.errorMessage = error.localizedDescription }
                    }
                    .disabled(store.state.plan == nil && store.state.history.isEmpty)
                    .opacity(store.state.plan == nil && store.state.history.isEmpty ? 0.4 : 1)
                    Text("数据仅保存在本机，建议定期导出留存。反馈文件用于分析，不是可导入的计划。")
                        .font(.caption).foregroundStyle(Theme.secondary)
                }
            }.padding(20).frame(maxWidth: 700).frame(maxWidth: .infinity)
        }
        .background(Theme.canvas).navigationTitle("记录").navigationBarTitleDisplayMode(.inline)
        .navigationDestination(for: WorkoutSession.self) { SessionDetailView(session: $0) }
        .navigationDestination(for: ProgressRoute.self) { ExerciseProgressView(exerciseID: $0.exerciseID) }
        .fileExporter(isPresented: $exporting, document: document, contentType: .json,
                      defaultFilename: "repcendo-feedback-\(Date.now.formatted(.iso8601.year().month().day().dateSeparator(.dash)))") { result in
            if case .failure(let error) = result { store.errorMessage = error.localizedDescription }
        }
    }
}

struct SessionDetailView: View {
    let session: WorkoutSession
    var body: some View {
        List {
            Section {
                Text(session.planName).font(.headline)
                Text("第 \(session.week) 周 · 计划版本 \(session.planRevision)").foregroundStyle(Theme.secondary)
                LabeledContent("完成组数", value: "\(session.completedSets) / \(session.totalSets)")
                LabeledContent("训练量", value: "\(weightText(session.volumeKg)) kg")
                if let end = session.finishedAt {
                    LabeledContent("时长（含暂停）", value: "\(max(1, Int(end.timeIntervalSince(session.startedAt) / 60))) 分钟")
                }
                if !session.notes.isEmpty { Text(session.notes) }
            }
            ForEach(session.exercises) { exercise in
                Section(exercise.name) {
                    ForEach(Array(exercise.sets.enumerated()), id: \.element.id) { index, set in
                        VStack(alignment: .leading, spacing: 6) {
                            Text(set.completed ? "第 \(index + 1) 组 · \(weightText(set.weightKg)) kg × \(set.reps ?? 0)\(set.rir.map { " · RIR \($0)" } ?? "")" : "第 \(index + 1) 组 · 未完成")
                                .font(.subheadline.weight(.medium))
                            if let target = set.target {
                                Text("原目标：\(target.repsLabel) · \(target.weightKg.map { "\(weightText($0)) kg" } ?? "重量自选")\(target.rir.map { " · RIR \($0)" } ?? "")")
                                    .font(.caption).foregroundStyle(Theme.secondary)
                            }
                        }.padding(.vertical, 4)
                    }
                }
            }
            Section("原计划快照") {
                ForEach(session.plannedWorkout.exercises) { original in
                    Text("\(original.displayName ?? original.exerciseID) · \(original.sets.count) 组")
                }
            }
        }.navigationTitle(session.plannedWorkout.name).navigationBarTitleDisplayMode(.inline)
    }
}

struct ProgressRoute: Hashable { let exerciseID: String }

struct ExerciseProgressView: View {
    @Environment(AppStore.self) private var store
    let exerciseID: String
    private var sessions: [WorkoutSession] {
        store.state.history.filter { $0.exercises.contains { $0.exerciseID == exerciseID && $0.sets.contains(where: \.completed) } }
    }
    private func sets(_ session: WorkoutSession) -> [LoggedSet] {
        session.exercises.filter { $0.exerciseID == exerciseID }.flatMap(\.sets).filter(\.completed)
    }
    var body: some View {
        List {
            if sessions.count > 1 {
                Section("每次训练的最高使用重量 · kg") {
                    Chart(sessions.reversed()) { session in
                        LineMark(x: .value("日期", session.startedAt), y: .value("最高重量", sets(session).compactMap(\.weightKg).max() ?? 0))
                            .symbol(.circle).foregroundStyle(Theme.accent)
                    }.frame(height: 180).padding(.vertical, 12)
                    Text("重量变化需要结合次数、RIR 和动作质量判断；不代表力量测试成绩。")
                        .font(.caption).foregroundStyle(Theme.secondary)
                }
            }
            ForEach(sessions) { session in
                Section(session.startedAt.formatted(date: .abbreviated, time: .omitted)) {
                    ForEach(sets(session)) { set in
                        Text("\(weightText(set.weightKg)) kg × \(set.reps ?? 0)\(set.rir.map { " · RIR \($0)" } ?? "")")
                            .monospacedDigit()
                    }
                }
            }
        }.navigationTitle(store.catalogByID[exerciseID]?.displayName ?? exerciseID)
    }
}
