function parsed = parse_options(args)
%PARSE_OPTIONS Turn a cell array of arguments into a request.
  parsed.status = 'ok';
  parsed.message = '';
  parsed.lines = false;
  parsed.words = false;
  parsed.bytes = false;
  parsed.any_figure = false;
  parsed.files = {};
  only_files = false;

  for index = 1:numel(args)
    arg = args{index};

    if ~strcmp(parsed.status, 'ok')
      break;
    end

    if only_files
      parsed.files{end + 1} = arg;
    elseif strcmp(arg, '--')
      only_files = true;
    elseif strcmp(arg, '--lines')
      parsed = show(parsed, 'lines');
    elseif strcmp(arg, '--words')
      parsed = show(parsed, 'words');
    elseif strcmp(arg, '--bytes')
      parsed = show(parsed, 'bytes');
    elseif strcmp(arg, '--help')
      parsed.status = 'help';
    elseif strcmp(arg, '--version')
      parsed.status = 'version';
    elseif strcmp(arg, '-')
      parsed.files{end + 1} = arg;
    elseif numel(arg) > 1 && arg(1) == '-'
      [parsed, ok] = parse_cluster(parsed, arg);
      if ~ok
        parsed.status = 'usage-error';
        parsed.message = sprintf('unknown option: %s', arg);
      end
    else
      parsed.files{end + 1} = arg;
    end
  end

  if strcmp(parsed.status, 'ok') && ~parsed.any_figure
    parsed = show(parsed, 'lines');
    parsed = show(parsed, 'words');
    parsed = show(parsed, 'bytes');
  end
end

function [parsed, ok] = parse_cluster(parsed, arg)
  ok = true;
  for letter = 2:numel(arg)
    switch arg(letter)
      case 'l'
        parsed = show(parsed, 'lines');
      case 'w'
        parsed = show(parsed, 'words');
      case 'c'
        parsed = show(parsed, 'bytes');
      case 'h'
        parsed.status = 'help';
        return;
      case 'V'
        parsed.status = 'version';
        return;
      otherwise
        ok = false;
        return;
    end
  end
end

function parsed = show(parsed, figure)
  parsed.(figure) = true;
  parsed.any_figure = true;
end
