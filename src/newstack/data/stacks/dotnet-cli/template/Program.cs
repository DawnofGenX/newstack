using {{ package_name }};

// A thin entry point: the exit code from Run becomes the process exit code.
return new Cli(Console.In, "{{ npm_name }}").Run(args, Console.Out, Console.Error);
