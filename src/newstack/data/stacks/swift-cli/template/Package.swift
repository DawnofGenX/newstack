// swift-tools-version:6.0
import PackageDescription

let package = Package(
    name: "TextStat",
    products: [
        .executable(name: "{{ npm_name }}", targets: ["TextStatCLI"]),
    ],
    targets: [
        .target(
            name: "TextStat"
        ),
        .executableTarget(
            name: "TextStatCLI",
            dependencies: ["TextStat"]
        ),
        .testTarget(
            name: "TextStatTests",
            dependencies: ["TextStat"]
        ),
    ]
)
