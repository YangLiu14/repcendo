import SwiftUI

enum Theme {
    static let accent = Color(uiColor: UIColor { traits in
        traits.userInterfaceStyle == .dark ? UIColor(red: 1, green: 0.65, blue: 0.33, alpha: 1) : UIColor(red: 0.66, green: 0.25, blue: 0.06, alpha: 1)
    })
    static let canvas = Color(uiColor: .systemGroupedBackground)
    static let surface = Color(uiColor: .secondarySystemGroupedBackground)
    static let ink = Color.primary
    static let secondary = Color(uiColor: UIColor { traits in
        traits.userInterfaceStyle == .dark ? UIColor(red: 0.74, green: 0.77, blue: 0.76, alpha: 1) : UIColor(red: 0.36, green: 0.39, blue: 0.38, alpha: 1)
    })
}

struct Card<Content: View>: View {
    @ViewBuilder var content: Content
    var body: some View {
        VStack(alignment: .leading, spacing: 16) { content }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(20).background(Theme.surface, in: RoundedRectangle(cornerRadius: 24))
    }
}

struct Eyebrow: View {
    let text: String
    var body: some View { Text(text).font(.caption.weight(.semibold)).tracking(2).foregroundStyle(Theme.accent) }
}

struct PrimaryButton: View {
    let title: String
    var icon: String = "arrow.right"
    let action: () -> Void
    var body: some View {
        Button(action: action) {
            HStack { Text(title).fontWeight(.semibold); Spacer(); Image(systemName: icon).accessibilityHidden(true) }
                .padding(.horizontal, 20).padding(.vertical, 16)
                .frame(minHeight: 52).foregroundStyle(Color(uiColor: .systemBackground))
                .background(Theme.accent, in: RoundedRectangle(cornerRadius: 16))
        }.buttonStyle(.plain)
    }
}

struct Metric: View {
    let value: String
    let label: String
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(value).font(.title2.weight(.semibold)).monospacedDigit()
            Text(label).font(.caption).foregroundStyle(Theme.secondary)
        }.frame(maxWidth: .infinity, alignment: .leading)
    }
}

enum ExerciseLabels {
    static let bodyParts = ["back": "背部", "cardio": "有氧", "chest": "胸部", "lower arms": "前臂", "lower legs": "小腿", "neck": "颈部", "shoulders": "肩部", "upper arms": "上臂", "upper legs": "大腿", "waist": "核心"]
    static let equipment = ["assisted": "辅助器械", "band": "弹力带", "barbell": "杠铃", "body weight": "自重", "bosu ball": "波速球", "cable": "绳索器械", "dumbbell": "哑铃", "elliptical machine": "椭圆机", "ez barbell": "曲杆杠铃", "hammer": "锤", "kettlebell": "壶铃", "leverage machine": "固定器械", "medicine ball": "药球", "olympic barbell": "奥林匹克杠铃", "resistance band": "阻力带", "roller": "滚筒", "rope": "绳", "skierg machine": "滑雪机", "sled machine": "雪橇机", "smith machine": "史密斯机", "stability ball": "健身球", "stationary bike": "健身单车", "stepmill machine": "爬楼机", "tire": "轮胎", "trap bar": "六角杠铃", "upper body ergometer": "上肢功率车", "weighted": "负重", "wheel roller": "健腹轮"]
    static func body(_ value: String) -> String { bodyParts[value] ?? value }
    static func gear(_ value: String) -> String { equipment[value] ?? value }
}

func weightText(_ value: Double?) -> String {
    guard let value else { return "—" }
    return value.formatted(.number.precision(.fractionLength(0...2)))
}
