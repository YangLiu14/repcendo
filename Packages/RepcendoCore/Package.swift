// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "RepcendoCore",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .library(name: "RepcendoCore", targets: ["RepcendoCore"]),
        .executable(name: "plan-check", targets: ["PlanCheck"])
    ],
    targets: [
        .target(name: "RepcendoCore"),
        .executableTarget(name: "PlanCheck", dependencies: ["RepcendoCore"]),
        .testTarget(name: "RepcendoCoreTests", dependencies: ["RepcendoCore"])
    ]
)
