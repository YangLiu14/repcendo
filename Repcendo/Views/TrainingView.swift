import SwiftUI
import RepcendoCore

struct WorkoutRoute: Hashable { let week: Int; let workout: PlannedWorkout }

struct TrainingView: View {
    @Environment(AppStore.self) private var store
    @State private var importing = false
    @State private var selectedWeek: Int?

    private var nextWorkout: WorkoutRoute? {
        guard let plan = store.state.plan else { return nil }
        for week in plan.weeks {
            for workout in week.workouts where !store.state.isCompleted(planID: plan.id, week: week.week, workoutID: workout.id) {
                return WorkoutRoute(week: week.week, workout: workout)
            }
        }
        return nil
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                VStack(alignment: .leading, spacing: 8) {
                    Eyebrow(text: "REPCENDO / 渐强")
                    Text("每一组，都有积累。").font(.largeTitle.bold())
                    Text(Date.now, format: .dateTime.month(.wide).day().weekday(.wide))
                        .font(.subheadline).foregroundStyle(Theme.secondary)
                }.padding(.top, 16)

                if let draft = store.state.draft {
                    Card {
                        Label("训练进行中 · 已自动保存", systemImage: "record.circle").font(.subheadline).foregroundStyle(Theme.accent)
                        Text(draft.plannedWorkout.name).font(.title2.bold())
                        Text("已完成 \(draft.completedSets) / \(draft.totalSets) 组").foregroundStyle(Theme.secondary)
                        PrimaryButton(title: "继续训练", icon: "play.fill") { store.showingWorkout = true }
                    }
                }

                if let plan = store.state.plan {
                    planContent(plan)
                } else {
                    welcome
                }
            }.padding(.horizontal, 20).padding(.bottom, 32).frame(maxWidth: 700)
                .frame(maxWidth: .infinity)
        }
        .background(Theme.canvas)
        .navigationTitle("训练").navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Menu {
                    Button("导入计划文件", systemImage: "square.and.arrow.down") { importing = true }
                    Button("查看示例计划", systemImage: "doc.text") { store.previewExample() }
                } label: { Label("计划操作", systemImage: "plus.circle").frame(minWidth: 44, minHeight: 44) }
            }
        }
        .fileImporter(isPresented: $importing, allowedContentTypes: [.json]) { result in
            switch result {
            case .success(let url): store.preview(url: url)
            case .failure(let error): store.errorMessage = error.localizedDescription
            }
        }
        .navigationDestination(for: WorkoutRoute.self) { WorkoutPlanView(route: $0) }
        .onChange(of: store.state.plan) { _, _ in selectedWeek = nil }
    }

    private var welcome: some View {
        VStack(spacing: 20) {
            Card {
                Image(systemName: "chart.line.uptrend.xyaxis").font(.system(size: 44, weight: .light))
                    .foregroundStyle(Theme.accent).padding(.vertical, 16).accessibilityHidden(true)
                Text("从一个会变化的\n计划开始。").font(.title.bold())
                Text("把 Codex 为你制定的计划带进来。训练时专注每一组，下一阶段再根据记录调整。")
                    .foregroundStyle(Theme.secondary).lineSpacing(5)
                PrimaryButton(title: "导入我的计划", icon: "square.and.arrow.down") { importing = true }
                Button("先体验示例计划") { store.previewExample() }
                    .frame(maxWidth: .infinity, minHeight: 44)
                    .accessibilityIdentifier("previewExample")
            }
            Card {
                Label("你的训练，由你掌握", systemImage: "arrow.triangle.2.circlepath").font(.headline)
                Label("每周目标可以不同", systemImage: "calendar")
                Label("记录重量、次数和剩余次数", systemImage: "checkmark.circle")
                Label("导出记录，交给 Codex 调整", systemImage: "square.and.arrow.up")
                Text("所有记录保存在这台设备，无需登录。")
                    .font(.footnote).foregroundStyle(Theme.secondary)
            }
        }
    }

    @ViewBuilder private func planContent(_ plan: TrainingPlan) -> some View {
        Card {
            HStack {
                Eyebrow(text: "当前周期")
                Spacer()
                Text("第 \(plan.revision) 版").font(.caption).foregroundStyle(Theme.secondary)
            }
            Text(plan.name).font(.title2.bold())
            if !plan.goal.isEmpty { Text(plan.goal).font(.subheadline).foregroundStyle(Theme.secondary) }
            let finished = plan.weeks.reduce(0) { sum, week in
                sum + week.workouts.filter { store.state.isCompleted(planID: plan.id, week: week.week, workoutID: $0.id) }.count
            }
            ProgressView(value: Double(finished), total: Double(plan.workoutCount)).accessibilityLabel("周期完成进度")
            HStack {
                Metric(value: "\(plan.weeks.count)", label: "计划周数")
                Metric(value: "\(finished) / \(plan.workoutCount)", label: "已完成训练")
            }
        }
        if store.state.draft == nil {
            if let next = nextWorkout {
                Card {
                    Eyebrow(text: "下一次训练 · 第 \(next.week) 周")
                    Text(next.workout.name).font(.title2.bold())
                    Text("\(next.workout.exercises.count) 个动作 · \(next.workout.setCount) 组")
                        .font(.subheadline).foregroundStyle(Theme.secondary)
                    PrimaryButton(title: "开始训练", icon: "play.fill") { store.begin(week: next.week, workout: next.workout) }
                        .accessibilityIdentifier("startWorkout")
                }
            } else {
                Card {
                    Label("这个周期，完成了。", systemImage: "checkmark.seal").font(.title3.bold())
                    Text("去「记录」导出你的表现，交给 Codex 制定下一阶段计划。")
                        .foregroundStyle(Theme.secondary)
                }
            }
        }
        VStack(alignment: .leading, spacing: 16) {
            Text("训练安排").font(.title3.bold())
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(plan.weeks) { week in
                        let active = (selectedWeek ?? nextWorkout?.week ?? 1) == week.week
                        Button { selectedWeek = week.week } label: {
                            Text("第 \(week.week) 周").font(.subheadline.weight(.semibold))
                                .padding(.horizontal, 18).frame(minHeight: 44)
                                .foregroundStyle(active ? Color(uiColor: .systemBackground) : Theme.ink)
                                .background(active ? Theme.accent : Theme.surface, in: Capsule())
                        }.buttonStyle(.plain).accessibilityAddTraits(active ? .isSelected : [])
                    }
                }
            }
            if let week = plan.weeks.first(where: { $0.week == (selectedWeek ?? nextWorkout?.week ?? 1) }) {
                Text(week.focus).font(.subheadline).foregroundStyle(Theme.secondary)
                ForEach(week.workouts) { workout in
                    NavigationLink(value: WorkoutRoute(week: week.week, workout: workout)) {
                        Card {
                            HStack(spacing: 16) {
                                let done = store.state.isCompleted(planID: plan.id, week: week.week, workoutID: workout.id)
                                Image(systemName: done ? "checkmark.circle.fill" : "dumbbell").foregroundStyle(Theme.accent).accessibilityHidden(true)
                                VStack(alignment: .leading, spacing: 6) {
                                    Text(workout.name).font(.headline).foregroundStyle(.primary)
                                    Text("\(workout.exercises.count) 动作 · \(workout.setCount) 组\(done ? " · 已完成" : "")")
                                        .font(.caption).foregroundStyle(Theme.secondary)
                                }
                                Spacer(minLength: 0)
                                Image(systemName: "chevron.right").font(.caption).foregroundStyle(Theme.secondary).accessibilityHidden(true)
                            }
                        }
                    }.buttonStyle(.plain)
                }
            }
        }
        if let notes = plan.notes, !notes.isEmpty {
            Text(notes).font(.footnote).foregroundStyle(Theme.secondary).lineSpacing(4)
        }
    }
}

struct WorkoutPlanView: View {
    @Environment(AppStore.self) private var store
    let route: WorkoutRoute
    var body: some View {
        List {
            Section {
                Text("第 \(route.week) 周 · \(route.workout.setCount) 组").foregroundStyle(Theme.accent)
                if let notes = route.workout.notes { Text(notes) }
            }
            ForEach(route.workout.exercises) { item in
                Section(store.exerciseName(item)) {
                    if let exercise = store.catalogByID[item.exerciseID] {
                        NavigationLink(value: exercise) { Label("查看动作说明", systemImage: "info.circle") }
                    }
                    TargetRows(sets: item.sets)
                    if let notes = item.notes { Text(notes).font(.footnote).foregroundStyle(Theme.secondary) }
                }
            }
        }
        .navigationTitle(route.workout.name)
        .navigationDestination(for: Exercise.self) { ExerciseDetailView(exercise: $0) }
        .safeAreaInset(edge: .bottom) {
            PrimaryButton(title: store.state.draft == nil ? "开始这次训练" : "继续正在进行的训练", icon: "play.fill") {
                store.begin(week: route.week, workout: route.workout)
            }.padding().background(.regularMaterial)
        }
    }
}

struct TargetRows: View {
    let sets: [SetTarget]
    var body: some View {
        ForEach(Array(sets.enumerated()), id: \.offset) { index, target in
            VStack(alignment: .leading, spacing: 4) {
                Text("第 \(index + 1) 组 · \(target.repsLabel)").font(.subheadline.weight(.medium))
                Text("\(target.weightKg.map { "\(weightText($0)) kg" } ?? "重量自选") · 休息 \(target.restSeconds) 秒\(target.rir.map { " · RIR \($0)" } ?? "")")
                    .font(.caption).foregroundStyle(Theme.secondary)
            }.padding(.vertical, 3)
        }
    }
}

struct ImportPreview: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    let plan: TrainingPlan
    private var obsolete: Bool {
        guard let current = store.state.plan else { return false }
        return current.id == plan.id && plan.revision <= current.revision
    }
    var body: some View {
        List {
            Section {
                Text(plan.name).font(.title2.bold())
                Text(plan.goal)
                Text("\(plan.weeks.count) 周 · \(plan.workoutCount) 次训练 · 第 \(plan.revision) 版").foregroundStyle(Theme.secondary)
                if let notes = plan.notes { Text(notes).font(.footnote).foregroundStyle(Theme.secondary) }
            }
            if obsolete {
                Section { Label("当前计划版本相同或更新，请让 Codex 提高 revision 后重新导入。", systemImage: "exclamationmark.circle").foregroundStyle(.red) }
            } else if store.state.plan != nil {
                Section {
                    Text(store.state.plan?.id == plan.id ? "这将更新当前计划。相同周数和训练 ID 的完成状态会保留。" : "这将切换到一个新的训练周期。")
                    Text("历史记录和正在进行的训练会完整保留。")
                }.font(.subheadline)
            }
            ForEach(plan.weeks) { week in
                Section("第 \(week.week) 周 · \(week.focus)") {
                    ForEach(week.workouts) { workout in
                        DisclosureGroup(workout.name) {
                            ForEach(workout.exercises) { item in
                                VStack(alignment: .leading, spacing: 8) {
                                    Text(store.exerciseName(item)).font(.headline)
                                    TargetRows(sets: item.sets)
                                }.padding(.vertical, 8)
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("确认训练计划").navigationBarTitleDisplayMode(.inline)
        .toolbar { ToolbarItem(placement: .cancellationAction) { Button("取消") { dismiss() } } }
        .safeAreaInset(edge: .bottom) {
            PrimaryButton(title: store.state.plan == nil ? "确认导入" : "确认更新", icon: "checkmark") { store.confirmImport() }
                .disabled(obsolete).opacity(obsolete ? 0.4 : 1).padding().background(.regularMaterial)
                .accessibilityIdentifier("confirmImport")
        }
    }
}
