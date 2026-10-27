import SwiftUI
import RepcendoCore

struct ExerciseLibraryView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    var onSelect: ((Exercise) -> Void)?
    @State private var query = ""
    @State private var bodyPart = ""
    @State private var equipment = ""
    private var filtered: [Exercise] {
        let search = query.trimmingCharacters(in: .whitespacesAndNewlines)
        return store.catalog.filter { exercise in
            (bodyPart.isEmpty || exercise.bodyPart == bodyPart) &&
            (equipment.isEmpty || exercise.equipment == equipment) &&
            (search.isEmpty || [exercise.name, exercise.displayName, exercise.id,
                               ExerciseLabels.body(exercise.bodyPart), ExerciseLabels.gear(exercise.equipment), exercise.target]
                .contains { $0.localizedCaseInsensitiveContains(search) })
        }
    }
    var body: some View {
        List {
            Section {
                Picker("肌群", selection: $bodyPart) {
                    Text("全部肌群").tag("")
                    ForEach(ExerciseLabels.bodyParts.keys.sorted(), id: \.self) { Text(ExerciseLabels.body($0)).tag($0) }
                }
                Picker("器械", selection: $equipment) {
                    Text("全部器械").tag("")
                    ForEach(ExerciseLabels.equipment.keys.sorted(), id: \.self) { Text(ExerciseLabels.gear($0)).tag($0) }
                }
            }
            Section("\(filtered.count) 个动作") {
                ForEach(filtered) { exercise in
                    if let onSelect {
                        Button { onSelect(exercise) } label: { ExerciseRow(exercise: exercise) }.tint(.primary)
                    } else {
                        NavigationLink(value: exercise) { ExerciseRow(exercise: exercise) }
                            .accessibilityIdentifier("exercise-\(exercise.id)")
                    }
                }
            }
        }
        .overlay {
            if filtered.isEmpty {
                ContentUnavailableView.search(text: query)
            }
        }
        .searchable(text: $query, prompt: "动作名称、器械或 ID")
        .navigationTitle(onSelect == nil ? "动作库" : "选择动作")
        .navigationDestination(for: Exercise.self) { ExerciseDetailView(exercise: $0) }
        .toolbar {
            if onSelect != nil { ToolbarItem(placement: .cancellationAction) { Button("取消") { dismiss() } } }
        }
    }
}

struct ExerciseRow: View {
    let exercise: Exercise
    var body: some View {
        HStack(spacing: 16) {
            Image(systemName: "dumbbell").font(.title3).foregroundStyle(Theme.accent)
                .frame(width: 44, height: 44).background(Theme.accent.opacity(0.08), in: RoundedRectangle(cornerRadius: 12))
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 6) {
                Text(exercise.displayName).font(.body.weight(.medium))
                Text("\(ExerciseLabels.body(exercise.bodyPart)) · \(ExerciseLabels.gear(exercise.equipment))")
                    .font(.caption).foregroundStyle(Theme.secondary)
            }.padding(.vertical, 6)
        }
    }
}

struct ExerciseDetailView: View {
    let exercise: Exercise
    var body: some View {
        List {
            Section {
                Text(exercise.displayName).font(.title2.bold())
                if exercise.localizedName != nil { Text(exercise.name).foregroundStyle(Theme.secondary) }
                LabeledContent("肌群", value: ExerciseLabels.body(exercise.bodyPart))
                LabeledContent("器械", value: ExerciseLabels.gear(exercise.equipment))
                LabeledContent("目标肌肉", value: exercise.target)
                LabeledContent("动作 ID", value: exercise.id).textSelection(.enabled)
            }
            Section("动作说明") {
                ForEach(Array(exercise.instructions.enumerated()), id: \.offset) { index, step in
                    HStack(alignment: .top, spacing: 16) {
                        Text(String(format: "%02d", index + 1)).font(.caption.monospaced().bold()).foregroundStyle(Theme.accent)
                            .padding(.top, 4).accessibilityHidden(true)
                        Text(step).lineSpacing(5)
                    }.padding(.vertical, 8)
                }
            }
            Section {
                Text("文字数据来源：exercises-dataset · MIT License").font(.footnote).foregroundStyle(Theme.secondary)
                NavigationLink("开源许可") {
                    ScrollView {
                        Text((Bundle.main.url(forResource: "DatasetLicense", withExtension: "txt").flatMap { try? String(contentsOf: $0, encoding: .utf8) }) ?? "")
                            .font(.footnote).textSelection(.enabled).padding()
                    }.navigationTitle("开源许可")
                }
            }
        }.navigationTitle("动作详情").navigationBarTitleDisplayMode(.inline)
    }
}
