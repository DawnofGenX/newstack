function handle_client(client)
%HANDLE_CLIENT Read one HTTP/1.1 request and write one response.
  input = client.getInputStream();
  head = uint8([]);
  body = uint8([]);
  while true
    b = input.read();
    if b < 0
      return;
    end
    head(end + 1) = uint8(b);
    if numel(head) >= 4 && isequal(head(end - 3:end), uint8([13 10 13 10]))
      break;
    end
    if numel(head) > 16384
      write_response(client, 431, uint8('{"error":"head_too_large"}'));
      return;
    end
  end

  lines = strsplit(char(head), sprintf('\r\n'));
  request = strsplit(lines{1}, ' ');
  if numel(request) < 3
    write_response(client, 400, uint8('{"error":"bad_request"}'));
    return;
  end
  method = request{1};
  target = request{2};

  want = 0;
  for i = 2:numel(lines)
    line = lines{i};
    mark = find(line == ':', 1);
    if isempty(mark)
      continue;
    end
    if strcmpi(strtrim(line(1:mark - 1)), 'content-length')
      want = str2double(strtrim(line(mark + 1:end)));
    end
  end
  if want > 65536
    write_response(client, 413, uint8('{"error":"body_too_large"}'));
    return;
  end

  while numel(body) < want
    b = input.read();
    if b < 0
      break;
    end
    body(end + 1) = uint8(b);
  end
  if numel(body) ~= want
    write_response(client, 400, uint8('{"error":"bad_request"}'));
    return;
  end

  [status, payload] = route(method, target, body);
  write_response(client, status, payload);
end

function write_response(client, status, payload)
  output = client.getOutputStream();
  head = sprintf(['HTTP/1.1 %d %s\r\n', ...
                  'content-type: application/json; charset=utf-8\r\n', ...
                  'content-length: %d\r\n', ...
                  'connection: close\r\n', ...
                  '\r\n'], status, reason(status), numel(payload));
  output.write(typecast(uint8(head), 'int8'));
  if ~isempty(payload)
    output.write(typecast(uint8(payload), 'int8'));
  end
  output.flush();
end

function text = reason(status)
  switch status
    case 200
      text = 'OK';
    case 400
      text = 'Bad Request';
    case 404
      text = 'Not Found';
    case 405
      text = 'Method Not Allowed';
    case 413
      text = 'Payload Too Large';
    case 422
      text = 'Unprocessable Content';
    case 431
      text = 'Request Header Fields Too Large';
    otherwise
      text = 'Internal Server Error';
  end
end
