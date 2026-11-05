const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // The service: src/main.zig wires the socket, src/server.zig speaks HTTP and
    // src/contract.zig decides the answer — so the routing is testable without a
    // network, and only the wire layer needs a real listener.
    const exe = b.addExecutable(.{
        .name = "{{ npm_name }}",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/main.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });
    b.installArtifact(exe);

    const run_step = b.step("run", "Run the service");
    const run_cmd = b.addRunArtifact(exe);
    run_cmd.step.dependOn(b.getInstallStep());
    run_step.dependOn(&run_cmd.step);

    // One test binary per module root: every file carries its own `test` blocks.
    const counting_tests = b.addTest(.{
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/counting.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });
    const contract_tests = b.addTest(.{
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/contract.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });
    const main_tests = b.addTest(.{ .root_module = exe.root_module });

    const test_step = b.step("test", "Run unit tests");
    test_step.dependOn(&b.addRunArtifact(counting_tests).step);
    test_step.dependOn(&b.addRunArtifact(contract_tests).step);
    test_step.dependOn(&b.addRunArtifact(main_tests).step);
}
