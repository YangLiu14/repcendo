import SwiftUI
import RepcendoCore

struct ExerciseLibraryView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    var onSelect: ((Exercise) -> Void)?
    var category: ExerciseCategory?
    @State private var query = ""
    @State private var target = ""
    @State private var equipment = ""
    @State private var showAll = false

    init(onSelect: ((Exercise) -> Void)? = nil, category: ExerciseCategory? = nil, initialEquipment: String = "") {
        self.onSelect = onSelect
        self.category = category
        _equipment = State(initialValue: initialEquipment)
    }

    private var scoped: [Exercise] {
        store.catalog.filter { category == nil || $0.category == category }
    }
    private var targets: [String] { Set(scoped.map(\.target)).sorted() }
    private var filtered: [Exercise] {
        let search = query.trimmingCharacters(in: .whitespacesAndNewlines)
        return scoped.filter { exercise in
            (target.isEmpty || exercise.target == target) &&
            (equipment.isEmpty || exercise.equipment == equipment) &&
            (search.isEmpty || [exercise.name, exercise.displayName, exercise.id,
                               exercise.category.title, exercise.targetDisplayName,
                               ExerciseLabels.gear(exercise.equipment),
                               exercise.bodyPart, exercise.equipment, exercise.target]
                .contains { $0.localizedCaseInsensitiveContains(search) })
        }
    }
    private var isBrowsingCategories: Bool {
        category == nil && !showAll && query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var body: some View {
        let items = filtered
        let groups = Dictionary(grouping: items, by: \.category)
        List {
            Section {
                Picker("器械", selection: $equipment) {
                    Text("全部器械").tag("")
                    ForEach(ExerciseLabels.equipment.keys.sorted(), id: \.self) { Text(ExerciseLabels.gear($0)).tag($0) }
                }.accessibilityIdentifier("equipmentFilter")
                if category != nil && targets.count > 1 {
                    Picker("目标肌肉", selection: $target) {
                        Text("全部目标肌肉").tag("")
                        ForEach(targets, id: \.self) { Text(Exercise.targetNames[$0] ?? $0).tag($0) }
                    }.accessibilityIdentifier("targetFilter")
                }
                if category == nil && query.isEmpty {
                    Toggle("展开全部动作", isOn: $showAll)
                }
            }
            if isBrowsingCategories {
                Section {
                    ForEach(ExerciseCategory.allCases.filter { groups[$0] != nil }) { part in
                        NavigationLink {
                            ExerciseLibraryView(onSelect: onSelect, category: part, initialEquipment: equipment)
                        } label: {
                            VStack(alignment: .leading, spacing: 6) {
                                HStack {
                                    Text(part.title).font(.headline)
                                    Spacer()
                                    Text("\(groups[part]?.count ?? 0) 个动作")
                                        .font(.subheadline).foregroundStyle(Theme.secondary)
                                }
                                Text(part.subtitle).font(.subheadline).foregroundStyle(Theme.secondary)
                            }.padding(.vertical, 8)
                        }.accessibilityIdentifier("category-\(part.rawValue)")
                    }
                } header: {
                    Text("按训练部位 · \(items.count) 个动作")
                } footer: {
                    Text("按数据集的主要目标肌肉归类，每个动作只计入一个部位；复合动作也可能训练其他肌群。")
                }
            } else {
                ForEach(ExerciseCategory.allCases.filter { groups[$0] != nil }) { part in
                    Section("\(part.title) · \(groups[part]?.count ?? 0) 个动作") {
                        ForEach(groups[part] ?? []) { exercise in
                            if let onSelect {
                                Button { onSelect(exercise) } label: { ExerciseRow(exercise: exercise) }
                                    .tint(.primary).accessibilityIdentifier("exercise-\(exercise.id)")
                            } else {
                                NavigationLink(value: exercise) { ExerciseRow(exercise: exercise) }
                                    .accessibilityIdentifier("exercise-\(exercise.id)")
                            }
                        }
                    }
                }
            }
            if items.isEmpty {
                Section {
                    ContentUnavailableView {
                        Label("没有符合条件的动作", systemImage: "magnifyingglass")
                    } description: {
                        Text("试试其他关键词，或清除器械和目标肌肉筛选。")
                    } actions: {
                        Button("清除搜索与筛选") { query = ""; equipment = ""; target = "" }
                    }
                }
            }
        }
        .searchable(text: $query, prompt: "搜索动作、部位、目标肌肉或 ID")
        .navigationTitle(category?.title ?? (onSelect == nil ? "动作库" : "选择动作"))
        .navigationDestination(for: Exercise.self) { ExerciseDetailView(exercise: $0) }
        .toolbar {
            if onSelect != nil && category == nil {
                ToolbarItem(placement: .cancellationAction) { Button("取消") { dismiss() } }
            }
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
                Text("\(exercise.targetDisplayName) · \(ExerciseLabels.gear(exercise.equipment))")
                    .font(.caption).foregroundStyle(Theme.secondary)
            }.padding(.vertical, 6)
        }
    }
}

struct ExerciseDetailView: View {
    let exercise: Exercise
    var body: some View {
        List {
            if let animation = ExerciseAnimation.catalog[exercise.id] {
                Section("动作示范") {
                    ExerciseAnimationView(animation: animation).id(exercise.id)
                }
            }
            Section {
                Text(exercise.displayName).font(.title2.bold())
                if exercise.localizedName != nil { Text(exercise.name).foregroundStyle(Theme.secondary) }
                LabeledContent("训练部位", value: exercise.category.title)
                LabeledContent("器械", value: ExerciseLabels.gear(exercise.equipment))
                LabeledContent("主要目标肌肉", value: exercise.targetDisplayName)
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
        }.navigationTitle("动作详情").navigationBarTitleDisplayMode(.inline)
    }
}
