// swift-tools-version:6.0
import PackageDescription

let package = Package(
    name: "Roman",
    products: [
        .executable(name: "{{ npm_name }}", targets: ["RomanCLI"]),
    ],
    targets: [
        .target(
            name: "Roman"
        ),
        .executableTarget(
            name: "RomanCLI",
            dependencies: ["Roman"]
        ),
        .testTarget(
            name: "RomanTests",
            dependencies: ["Roman"]
        ),
    ]
)
