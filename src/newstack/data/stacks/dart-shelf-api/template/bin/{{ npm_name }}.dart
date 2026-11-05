// ignore_for_file: file_names
// The entry file is named after the project, and project names may contain hyphens
// (a directory name is not a Dart identifier).
import "dart:io";

import "package:shelf/shelf_io.dart" as shelf_io;
import "package:{{ package_name }}/{{ package_name }}.dart";

/// Serves the service. `PORT` picks the port and `ADDR` the interface; both default to
/// something a laptop can run without exposing a port to the network.
Future<void> main(List<String> args) async {
  final port = int.tryParse(Platform.environment["PORT"] ?? "") ?? 8080;
  final address = Platform.environment["ADDR"] ?? "127.0.0.1";
  final server = await shelf_io.serve(buildHandler(), address, port);
  stdout.writeln("listening on http://${server.address.host}:${server.port}");

  Future<void> stop(ProcessSignal signal) async {
    stdout.writeln("${signal.name}: stopping");
    await server.close(force: false);
    exit(0);
  }

  ProcessSignal.sigint.watch().listen(stop);
  if (!Platform.isWindows) {
    ProcessSignal.sigterm.watch().listen(stop);
  }
}
