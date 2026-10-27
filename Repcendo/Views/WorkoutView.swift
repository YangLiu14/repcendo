import SwiftUI
import RepcendoCore

struct WorkoutView: View {
    @Environment(AppStore.self) private var store
    @State private var pickingExercise = false
    @State private var replacingExercise: UUID?
    @State private var confirmingFinish = false
    @State private var confirmingDiscard = false
    @State private var exerciseToRemove: UUID?

    var body: some View {
        Group {
            if let draft = store.state.draft {
                List {
                    Section {
                        VStack(alignment: .leading, spacing: 12) {
                            Eyebrow(text: "第 \(draft.week) 周 · \(draft.planName)")
                            HStack {
                                Text("\(draft.completedSets)").font(.largeTitle.bold()).monospacedDigit()
                                Text("/ \(draft.totalSets) 组已完成").foregroundStyle(Theme.secondary)
                            }
                            ProgressView(value: Double(draft.completedSets), total: Double(max(1, draft.totalSets)))
                            Text("填写实际表现，再点圆圈完成。RIR 表示这组结束时还能做几次，可留空。")
                                .font(.footnote).foregroundStyle(Theme.secondary)
                        }.padding(.vertical, 8)
                    }
                    if let deadline = draft.restEndsAt {
                        Section { RestTimer(deadline: deadline) { store.editDraft { $0.restEndsAt = nil } } }
                    }
                    ForEach(draft.exercises) { exercise in
                        Section {
                            if let detail = store.catalogByID[exercise.exerciseID] {
                                NavigationLink(value: detail) { Label("动作说明", systemImage: "info.circle").font(.subheadline) }
                            }
                            if let original = draft.plannedWorkout.exercises.first(where: { $0.id == exercise.sourceSlotID }),
                               original.exerciseID != exercise.exerciseID {
                                Text("原计划：\(store.exerciseName(original))").font(.caption).foregroundStyle(Theme.secondary)
                            }
                            let previous = store.previousSets(for: exercise.exerciseID)
                            ForEach(Array(exercise.sets.enumerated()), id: \.element.id) { index, set in
                                SetEditor(exerciseID: exercise.id, index: index, set: set,
                                          previous: previous.indices.contains(index) ? previous[index] : nil)
                            }
                            Button("增加一组", systemImage: "plus") { store.addSet(exerciseID: exercise.id) }
                                .frame(minHeight: 44).disabled(exercise.sets.count >= 30)
                        } header: {
                            HStack(alignment: .center) {
                                Text(exercise.name).font(.headline).textCase(nil).foregroundStyle(.primary)
                                Spacer()
                                Menu {
                                    Button("替换动作", systemImage: "arrow.triangle.2.circlepath") {
                                        replacingExercise = exercise.id; pickingExercise = true
                                    }.disabled(exercise.sets.contains(where: \.completed))
                                    Button("移除此动作", systemImage: "trash", role: .destructive) { exerciseToRemove = exercise.id }
                                } label: {
                                    Image(systemName: "ellipsis.circle").frame(minWidth: 44, minHeight: 44)
                                }.accessibilityLabel("\(exercise.name)操作")
                            }
                        } footer: {
                            if let original = draft.plannedWorkout.exercises.first(where: { $0.id == exercise.sourceSlotID }), let notes = original.notes {
                                Text(notes)
                            }
                        }
                    }
                    Section {
                        Button("添加动作", systemImage: "plus.circle") { replacingExercise = nil; pickingExercise = true }
                            .frame(minHeight: 44).disabled(draft.exercises.count >= 30)
                        TextField("训练备注：状态、动作替换原因…", text: Binding(get: { store.state.draft?.notes ?? "" },
                                                                                 set: { value in store.editDraft { $0.notes = value } }), axis: .vertical)
                            .lineLimit(3...6).accessibilityIdentifier("sessionNotes")
                    }
                    Section {
                        Button("放弃本次训练", role: .destructive) { confirmingDiscard = true }.frame(minHeight: 44)
                    }
                }
                .navigationTitle(draft.plannedWorkout.name).navigationBarTitleDisplayMode(.inline)
                .safeAreaInset(edge: .bottom) {
                    PrimaryButton(title: "结束训练", icon: "checkmark") { confirmingFinish = true }
                        .disabled(draft.completedSets == 0).opacity(draft.completedSets == 0 ? 0.4 : 1)
                        .padding().background(.regularMaterial).accessibilityIdentifier("finishWorkout")
                }
            }
        }
        .toolbar {
            ToolbarItem(placement: .cancellationAction) { Button("稍后继续") { store.showingWorkout = false } }
            ToolbarItemGroup(placement: .keyboard) {
                Spacer()
                Button("收起键盘") { UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil) }
            }
        }
        .navigationDestination(for: Exercise.self) { ExerciseDetailView(exercise: $0) }
        .sheet(isPresented: $pickingExercise) {
            NavigationStack {
                ExerciseLibraryView { exercise in
                    store.chooseExercise(exercise, replacing: replacingExercise); pickingExercise = false
                }
            }
        }
        .alert("完成这次训练？", isPresented: $confirmingFinish) {
            Button("继续记录", role: .cancel) {}
            Button("保存并结束") { store.finish() }
        } message: {
            Text("已完成 \(store.state.draft?.completedSets ?? 0) / \(store.state.draft?.totalSets ?? 0) 组。未完成的组会保留为未完成，不计入训练量。")
        }
        .confirmationDialog("放弃后会删除本次草稿，无法恢复。", isPresented: $confirmingDiscard, titleVisibility: .visible) {
            Button("放弃训练", role: .destructive) { store.discard() }
        }
        .confirmationDialog("移除此动作及本次记录的所有组？", isPresented: Binding(get: { exerciseToRemove != nil }, set: { if !$0 { exerciseToRemove = nil } }), titleVisibility: .visible) {
            Button("移除动作", role: .destructive) { if let id = exerciseToRemove { store.removeExercise(id: id) }; exerciseToRemove = nil }
        }
    }
}

struct SetEditor: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize
    let exerciseID: UUID
    let index: Int
    let set: LoggedSet
    let previous: LoggedSet?
    @State private var weight = ""
    @State private var reps = ""
    @State private var rir = ""
    @State private var hydrated = false
    @State private var confirmingDelete = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 5) {
                    Text("第 \(index + 1) 组\(set.completed ? " · 已完成" : "")").font(.subheadline.weight(.semibold))
                    if let target = set.target {
                        Text("目标 \(target.repsLabel) · \(target.weightKg.map { "\(weightText($0)) kg" } ?? "重量自选")\(target.rir.map { " · RIR \($0)" } ?? "")")
                            .font(.caption).foregroundStyle(Theme.secondary)
                    } else { Text("临时增加的训练组").font(.caption).foregroundStyle(Theme.secondary) }
                }
                Spacer(minLength: 0)
                Button { confirmingDelete = true } label: {
                    Image(systemName: "minus.circle").frame(width: 44, height: 44).foregroundStyle(Theme.secondary)
                }.buttonStyle(.borderless).accessibilityLabel("删除第 \(index + 1) 组")
            }
            if dynamicTypeSize.isAccessibilitySize {
                VStack(alignment: .leading, spacing: 12) { fields; completeButton }
            } else {
                HStack(alignment: .bottom, spacing: 8) { fields; completeButton }
            }
            if let previous {
                HStack {
                    Text("上次 \(weightText(previous.weightKg)) kg × \(previous.reps ?? 0)\(previous.rir.map { " · RIR \($0)" } ?? "")")
                        .font(.caption).foregroundStyle(Theme.secondary)
                    Spacer(minLength: 0)
                    Button("沿用") {
                        weight = previous.weightKg.map { String($0) } ?? ""
                        reps = previous.reps.map(String.init) ?? ""
                        rir = ""
                    }.font(.caption.weight(.semibold)).frame(minWidth: 44, minHeight: 44).disabled(set.completed)
                        .buttonStyle(.borderless).accessibilityLabel("沿用第 \(index + 1) 组上次的重量和次数")
                }
            }
        }
        .padding(.vertical, 8)
        .onAppear {
            weight = set.weightKg.map { String($0) } ?? ""
            reps = set.reps.map(String.init) ?? ""
            rir = set.rir.map(String.init) ?? ""
            hydrated = true
        }
        .onChange(of: weight) { _, _ in persist() }
        .onChange(of: reps) { _, _ in persist() }
        .onChange(of: rir) { _, _ in persist() }
        .confirmationDialog("删除第 \(index + 1) 组及已填数据？", isPresented: $confirmingDelete, titleVisibility: .visible) {
            Button("删除这一组", role: .destructive) { store.removeSet(exerciseID: exerciseID, setID: set.id) }
        }
    }

    @ViewBuilder private var fields: some View {
        field("重量 kg", value: $weight, placeholder: "0", keyboard: .decimalPad, identifier: "weight-\(index)")
        field("次数", value: $reps, placeholder: "次数", keyboard: .numberPad, identifier: "reps-\(index)")
        field("RIR", value: $rir, placeholder: "选填", keyboard: .numberPad, identifier: "rir-\(index)")
    }

    private func field(_ label: String, value: Binding<String>, placeholder: String, keyboard: UIKeyboardType, identifier: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label).font(.caption).foregroundStyle(Theme.secondary)
            TextField(placeholder, text: value).keyboardType(keyboard)
                .font(.body.monospacedDigit()).padding(10).frame(minWidth: 58, minHeight: 48)
                .background(Theme.canvas, in: RoundedRectangle(cornerRadius: 10))
                .disabled(set.completed).accessibilityLabel("第 \(index + 1) 组\(label)")
                .accessibilityIdentifier(identifier)
        }
    }

    private var completeButton: some View {
        Button {
            if !set.completed && !rir.isEmpty && Int(rir) == nil {
                store.errorMessage = "RIR 请填写 0–10 的整数，或留空。"
                return
            }
            store.toggleSet(exerciseID: exerciseID, setID: set.id)
        } label: {
            Image(systemName: set.completed ? "checkmark.circle.fill" : "circle")
                .font(.system(size: 30, weight: .light)).foregroundStyle(set.completed ? Theme.accent : Theme.secondary)
                .frame(minWidth: 48, minHeight: 48)
        }.buttonStyle(.borderless).accessibilityLabel(set.completed ? "取消完成第 \(index + 1) 组" : "完成第 \(index + 1) 组")
            .accessibilityIdentifier("completeSet-\(index)")
    }

    private func persist() {
        guard hydrated else { return }
        store.editSet(exerciseID: exerciseID, setID: set.id) { actual in
            actual.weightKg = Double(weight.replacingOccurrences(of: ",", with: ".")).flatMap { $0.isFinite ? $0 : nil }
            actual.reps = Int(reps); actual.rir = rir.isEmpty ? nil : Int(rir)
        }
    }
}

struct RestTimer: View {
    let deadline: Date
    let stop: () -> Void
    var body: some View {
        TimelineView(.periodic(from: .now, by: 1)) { context in
            let seconds = max(0, Int(ceil(deadline.timeIntervalSince(context.date))))
            HStack {
                Label(seconds > 0 ? "组间休息" : "休息结束", systemImage: "timer").font(.subheadline)
                Spacer()
                Text(String(format: "%02d:%02d", seconds / 60, seconds % 60)).font(.title2.monospacedDigit().bold())
                Button("结束", action: stop).frame(minWidth: 44, minHeight: 44).buttonStyle(.borderless)
            }.foregroundStyle(Theme.accent)
        }
    }
}
