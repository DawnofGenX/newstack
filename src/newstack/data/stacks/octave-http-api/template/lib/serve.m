function serve(host, port)
%SERVE Accept connections one at a time and answer each with route/3.
  server = javaObject('java.net.ServerSocket');
  server.setReuseAddress(true);
  address = javaObject('java.net.InetSocketAddress', host, port);
  server.bind(address, 64);
  printf('listening on http://%s:%d\n', host, port);
  fflush(stdout);
  while true
    client = server.accept();
    try
      handle_client(client);
    catch err
      printf('request failed: %s\n', err.message);
      fflush(stdout);
    end
    client.close();
  end
end
