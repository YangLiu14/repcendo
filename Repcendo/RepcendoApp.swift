import SwiftUI
import UniformTypeIdentifiers
import RepcendoCore

@main
struct RepcendoApp: App {
    @State private var store = AppStore()
    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(store)
                .tint(Theme.accent)
                .onOpenURL { store.preview(url: $0) }
        }
    }
}

struct RootView: View {
    @Environment(AppStore.self) private var store
    @State private var selectedTab = 0
    var body: some View {
        @Bindable var store = store
        Group {
            if let error = store.startupError {
                ContentUnavailableView {
                    Label("数据暂时无法打开", systemImage: "externaldrive.badge.exclamationmark")
                } description: { Text(error) } actions: {
                    if FileManager.default.fileExists(atPath: store.dataFileURL.path) {
                        ShareLink("导出原始数据", item: store.dataFileURL)
                    }
                }
            } else {
                TabView(selection: $selectedTab) {
                    NavigationStack { TrainingView() }.tabItem { Label("训练", systemImage: "dumbbell") }.tag(0)
                    NavigationStack { ExerciseLibraryView() }.tabItem { Label("动作库", systemImage: "square.grid.2x2") }.tag(1)
                    NavigationStack { HistoryView() }.tabItem { Label("记录", systemImage: "chart.xyaxis.line") }.tag(2)
                }
                .sheet(item: $store.pendingPlan) { plan in
                    NavigationStack { ImportPreview(plan: plan) }
                        .modifier(AppErrorAlert())
                }
                .fullScreenCover(isPresented: $store.showingWorkout) {
                    NavigationStack { WorkoutView() }
                        .modifier(AppErrorAlert())
                }
            }
        }
        .modifier(AppErrorAlert(isActive: !store.showingWorkout && store.pendingPlan == nil))
    }
}

struct AppErrorAlert: ViewModifier {
    @Environment(AppStore.self) private var store
    var isActive = true
    func body(content: Content) -> some View {
        content.alert("操作未完成", isPresented: Binding(get: { isActive && store.errorMessage != nil }, set: { if !$0 && isActive { store.errorMessage = nil } })) {
            Button("知道了", role: .cancel) { store.errorMessage = nil }
        } message: { Text(store.errorMessage ?? "") }
    }
}

struct JSONDocument: FileDocument {
    static var readableContentTypes: [UTType] { [.json] }
    var data: Data
    init(data: Data) { self.data = data }
    init(configuration: ReadConfiguration) throws { data = configuration.file.regularFileContents ?? Data() }
    func fileWrapper(configuration: WriteConfiguration) throws -> FileWrapper { FileWrapper(regularFileWithContents: data) }
}
