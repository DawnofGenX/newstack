function [status, body] = route(method, target, rawbody)
%ROUTE Answer one request. status is a number, body a uint8 vector.
  mark = find(target == '?', 1);
  if isempty(mark)
    path = target;
    query = '';
  else
    path = target(1:mark - 1);
    query = target(mark + 1:end);
  end
  isstats = strcmp(path, '/stats');
  if strcmp(path, '/health')
    if ~strcmp(method, 'GET')
      [status, body] = fail(405, 'method_not_allowed');
      return;
    end
    status = 200;
    body = uint8('{"status":"ok"}');
    return;
  elseif ~isstats
    status = 404;
    body = [uint8('{"error":"not_found","detail":"no route for '), ...
            uint8(method), uint8(' '), json_escape_text(target), uint8('"}')];
    return;
  end

  if strcmp(method, 'GET')
    [found, value] = first_param(query, 'text');
    if ~found
      [status, body] = fail(422, 'missing_text');
      return;
    end
    raw = percent_decode(value);
  elseif strcmp(method, 'POST')
    [kind, raw] = jsonread(rawbody);
    if strcmp(kind, 'missing')
      [status, body] = fail(422, 'missing_text');
      return;
    elseif ~strcmp(kind, 'text')
      [status, body] = fail(422, 'invalid_json');
      return;
    end
  else
    [status, body] = fail(405, 'method_not_allowed');
    return;
  end

  [lines, words, nbytes] = counts(raw);
  status = 200;
  body = [uint8('{"text":'), json_quote(raw), ...
          uint8(sprintf(',"lines":%d,"words":%d,"bytes":%d}', lines, words, nbytes))];
end

function [status, body] = fail(code, code_name)
  status = code;
  body = [uint8('{"error":"'), uint8(code_name), uint8('"}')];
end

function [found, value] = first_param(query, name)
  found = false;
  value = uint8([]);
  if isempty(query)
    return;
  end
  parts = strsplit(query, '&');
  for i = 1:numel(parts)
    pair = parts{i};
    eq = find(pair == '=', 1);
    if isempty(eq)
      key = pair;
      val = '';
    else
      key = pair(1:eq - 1);
      val = pair(eq + 1:end);
    end
    if strcmp(char(percent_decode(key)), name)
      found = true;
      value = uint8(val);
      return;
    end
  end
end

function out = json_escape_text(bytes)
  quoted = json_quote(uint8(bytes));
  out = quoted(2:end - 1);
end
