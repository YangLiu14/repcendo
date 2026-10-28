import Foundation

/// A single browsing category per exercise, derived from the upstream primary target.
/// This does not describe every muscle involved in a compound movement.
public enum ExerciseCategory: String, CaseIterable, Identifiable {
    case chest, back, shoulders, upperArms, forearms, glutes, thighs, calves, core, neck, cardio, other

    public var id: String { rawValue }

    public var title: String {
        switch self {
        case .chest: return "胸部"
        case .back: return "背部"
        case .shoulders: return "肩部"
        case .upperArms: return "上臂"
        case .forearms: return "前臂"
        case .glutes: return "臀部"
        case .thighs: return "大腿"
        case .calves: return "小腿"
        case .core: return "核心"
        case .neck: return "颈部"
        case .cardio: return "有氧"
        case .other: return "其他"
        }
    }

    public var subtitle: String {
        switch self {
        case .chest: return "胸肌、前锯肌"
        case .back: return "背阔肌、上背、斜方肌、竖脊肌"
        case .shoulders: return "三角肌"
        case .upperArms: return "肱二头肌、肱三头肌"
        case .forearms: return "前臂肌群"
        case .glutes: return "臀肌"
        case .thighs: return "股四头肌、腘绳肌、内收肌群、外展肌群"
        case .calves: return "小腿肌群"
        case .core: return "腹肌"
        case .neck: return "肩胛提肌"
        case .cardio: return "心肺训练"
        case .other: return "尚未分类的动作"
        }
    }
}

public extension Exercise {
    var category: ExerciseCategory {
        if target == "glutes" { return .glutes }
        switch bodyPart {
        case "chest": return .chest
        case "back": return .back
        case "shoulders": return .shoulders
        case "upper arms": return .upperArms
        case "lower arms": return .forearms
        case "upper legs": return .thighs
        case "lower legs": return .calves
        case "waist": return .core
        case "neck": return .neck
        case "cardio": return .cardio
        default: return .other
        }
    }

    var targetDisplayName: String { Self.targetNames[target] ?? target }

    static let targetNames = [
        "pectorals": "胸肌", "serratus anterior": "前锯肌", "lats": "背阔肌",
        "upper back": "上背肌群", "spine": "竖脊肌", "traps": "斜方肌",
        "delts": "三角肌", "biceps": "肱二头肌", "triceps": "肱三头肌",
        "forearms": "前臂肌群", "glutes": "臀肌", "quads": "股四头肌",
        "hamstrings": "腘绳肌", "adductors": "内收肌群", "abductors": "外展肌群",
        "calves": "小腿肌群", "abs": "腹肌", "levator scapulae": "肩胛提肌",
        "cardiovascular system": "心肺系统"
    ]
}
