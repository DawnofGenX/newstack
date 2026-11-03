const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // The CLI: src/main.zig parses argv and does the I/O, src/counting.zig holds
    // the pure counting logic so it can be tested without touching a file.
    const exe = b.addExecutable(.{
        .name = "{{ package_name }}",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/main.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });
    b.installArtifact(exe);

    const run_step = b.step("run", "Run the app");
    const run_cmd = b.addRunArtifact(exe);
    run_cmd.step.dependOn(b.getInstallStep());
    run_cmd.addPassthruArgs();
    run_step.dependOn(&run_cmd.step);

    // One test binary per module root: both files carry `test` blocks.
    const counting_tests = b.addTest(.{
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/counting.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });
    const exe_tests = b.addTest(.{ .root_module = exe.root_module });

    const test_step = b.step("test", "Run unit tests");
    test_step.dependOn(&b.addRunArtifact(counting_tests).step);
    test_step.dependOn(&b.addRunArtifact(exe_tests).step);
}
