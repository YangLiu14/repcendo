import SwiftUI
import AVFoundation
import Combine

struct ExerciseAnimation: Decodable {
    struct Variant: Decodable {
        let video: String
        let poster: String
    }
    let title: String
    let variants: [String: Variant]

    static let catalog: [String: ExerciseAnimation] = {
        guard let url = resource("catalog.json"), let data = try? Data(contentsOf: url),
              let catalog = try? JSONDecoder().decode([String: ExerciseAnimation].self, from: data) else { return [:] }
        return catalog
    }()

    static func resource(_ name: String) -> URL? {
        Bundle.main.url(forResource: name, withExtension: nil, subdirectory: "ExerciseAnimations")
    }
}

@MainActor
private final class ExercisePlayback: ObservableObject {
    let player = AVQueuePlayer()
    @Published private(set) var isPlaying = false
    @Published private(set) var hasStarted = false
    @Published private(set) var error: String?
    private var looper: AVPlayerLooper?
    private var wantsPlayback = false
    private var observations = Set<AnyCancellable>()

    init() {
        player.isMuted = true
        player.publisher(for: \.timeControlStatus)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] in self?.isPlaying = $0 == .playing }
            .store(in: &observations)
        player.publisher(for: \.currentItem)
            .map { item -> AnyPublisher<AVPlayerItem.Status, Never> in
                item?.publisher(for: \.status).eraseToAnyPublisher()
                    ?? Just(.unknown).eraseToAnyPublisher()
            }
            .switchToLatest()
            .receive(on: DispatchQueue.main)
            .sink { [weak self] status in
                if status == .failed {
                    self?.pause()
                    self?.error = "暂时无法播放示范，请重试。"
                } else if status == .readyToPlay, self?.wantsPlayback == true {
                    // The looper inserts its first item asynchronously on initial loading.
                    self?.player.play()
                }
            }
            .store(in: &observations)
    }

    func load(_ variant: ExerciseAnimation.Variant?) {
        unload()
        error = nil
        guard let variant, let url = ExerciseAnimation.resource(variant.video) else {
            error = "未找到离线示范视频。"
            return
        }
        looper = AVPlayerLooper(player: player, templateItem: AVPlayerItem(url: url))
        play()
    }

    func play() {
        guard error == nil else { return }
        wantsPlayback = true
        hasStarted = true
        player.play()
    }

    func pause() { wantsPlayback = false; player.pause(); isPlaying = false }

    func replay() {
        player.seek(to: .zero, toleranceBefore: .zero, toleranceAfter: .zero)
        play()
    }

    func unload() {
        pause()
        looper?.disableLooping()
        looper = nil
        player.removeAllItems()
        hasStarted = false
    }
}

private struct ExerciseVideoSurface: UIViewRepresentable {
    let player: AVPlayer

    final class Surface: UIView {
        override class var layerClass: AnyClass { AVPlayerLayer.self }
        var videoLayer: AVPlayerLayer { layer as! AVPlayerLayer }
    }

    func makeUIView(context: Context) -> Surface {
        let view = Surface()
        view.videoLayer.videoGravity = .resizeAspect
        view.videoLayer.player = player
        return view
    }

    func updateUIView(_ view: Surface, context: Context) { view.videoLayer.player = player }
    static func dismantleUIView(_ view: Surface, coordinator: ()) { view.videoLayer.player = nil }
}

struct ExerciseAnimationView: View {
    let animation: ExerciseAnimation
    @Environment(\.scenePhase) private var scenePhase
    @AppStorage("exerciseAnimationCharacter") private var character = "male"
    @StateObject private var playback = ExercisePlayback()
    @State private var isFullScreen = false
    private var variant: ExerciseAnimation.Variant? { animation.variants[character] }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Picker("示范人物", selection: $character) {
                Text("男性").tag("male")
                Text("女性").tag("female")
            }.pickerStyle(.segmented).accessibilityIdentifier("animationCharacter")

            Button {
                isFullScreen = true
                playback.play()
            } label: {
                ZStack(alignment: .bottomTrailing) {
                    if !isFullScreen {
                        ExerciseVideoSurface(player: playback.player)
                    } else {
                        Color.black
                    }
                    if !playback.hasStarted,
                       let name = variant?.poster, let url = ExerciseAnimation.resource(name),
                       let poster = UIImage(contentsOfFile: url.path) {
                        Image(uiImage: poster).resizable().scaledToFit()
                    }
                    Image(systemName: "arrow.up.left.and.arrow.down.right")
                        .padding(10).foregroundStyle(.white).background(.black.opacity(0.65), in: Circle())
                        .padding(10)
                }
                .aspectRatio(4 / 3, contentMode: .fit)
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            .buttonStyle(.plain)
            .accessibilityLabel("全屏播放\(animation.title)")
            .accessibilityIdentifier("animationFullScreen")

            if let error = playback.error {
                Text(error).font(.subheadline).foregroundStyle(Theme.secondary)
                Button("重新加载") { playback.load(variant) }.frame(minHeight: 44)
            } else {
                HStack(spacing: 24) {
                    Button {
                        if playback.isPlaying { playback.pause() } else { playback.play() }
                    } label: {
                        Label(playback.isPlaying ? "暂停" : "播放", systemImage: playback.isPlaying ? "pause.fill" : "play.fill")
                    }.frame(minHeight: 44).accessibilityIdentifier("animationPlayPause")
                    Button { playback.replay() } label: { Label("重播", systemImage: "arrow.counterclockwise") }
                        .frame(minHeight: 44).accessibilityIdentifier("animationReplay")
                }.buttonStyle(.borderless)
            }
        }
        .onAppear {
            if animation.variants[character] == nil { character = "male" }
            if playback.player.currentItem == nil { playback.load(variant) }
        }
        .onChange(of: character) { _, _ in playback.load(variant) }
        .onChange(of: scenePhase) { _, phase in if phase != .active { playback.pause() } }
        .onDisappear { if !isFullScreen { playback.unload() } }
        .fullScreenCover(isPresented: $isFullScreen) {
            FullScreenExerciseAnimation(playback: playback, title: animation.title)
        }
    }
}

private struct FullScreenExerciseAnimation: View {
    @ObservedObject var playback: ExercisePlayback
    let title: String
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            ExerciseVideoSurface(player: playback.player)
                .accessibilityHidden(true)
        }
        .safeAreaInset(edge: .top) {
            HStack {
                Text(title).font(.headline)
                Spacer()
                Button { dismiss() } label: {
                    Label("退出全屏", systemImage: "xmark")
                        .frame(minHeight: 44)
                }.accessibilityIdentifier("animationExitFullScreen")
            }.padding(.horizontal).foregroundStyle(.white).background(.black)
        }
        .safeAreaInset(edge: .bottom) {
            HStack(spacing: 32) {
                Button {
                    if playback.isPlaying { playback.pause() } else { playback.play() }
                } label: {
                    Label(playback.isPlaying ? "暂停" : "播放", systemImage: playback.isPlaying ? "pause.fill" : "play.fill")
                        .frame(minHeight: 44)
                }.accessibilityIdentifier("fullScreenPlayPause")
                Button { playback.replay() } label: {
                    Label("重播", systemImage: "arrow.counterclockwise").frame(minHeight: 44)
                }.accessibilityIdentifier("fullScreenReplay")
            }.padding().frame(maxWidth: .infinity).foregroundStyle(.white).background(.black)
        }
    }
}
