% Text statistics service: GET /health, GET|POST /stats.
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, 'lib'));

if strcmp(getenv('TEXTSTAT_SELFTEST'), '1')
  ok = selftest();
  exit(ok);
end

port = 8080;
raw = getenv('PORT');
if ~isempty(raw)
  port = str2double(raw);
  if isnan(port) || port <= 0 || port > 65535 || port ~= floor(port)
    fprintf(2, 'PORT must be an integer between 1 and 65535, got %s\n', raw);
    exit(2);
  end
end
host = getenv('HOST');
if isempty(host)
  host = '127.0.0.1';
end
serve(host, port);
