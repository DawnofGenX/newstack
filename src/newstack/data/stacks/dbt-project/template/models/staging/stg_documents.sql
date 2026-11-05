-- Seeds cannot carry a real newline without quoting a multi-line CSV field, so the seed
-- stores the two characters `\` + `n` and staging turns them into chr(10). Everything
-- downstream sees the same text a program would.
select
    id,
    title,
    replace(raw_text, '\n', chr(10)) as text
from {{ ref('documents') }}
