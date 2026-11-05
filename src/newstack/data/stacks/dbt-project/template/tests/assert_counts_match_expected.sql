-- A singular test that fails by returning rows. The expected numbers are the ones in the
-- README's table, so the documentation and the build cannot drift apart.
select *
from {{ ref('doc_stats') }}
where
    (id = 1 and (lines <> 1 or words <> 2 or bytes <> 12))
    or (id = 2 and (lines <> 2 or words <> 3 or bytes <> 6))
    or (id = 3 and (lines <> 1 or words <> 1 or bytes <> 11))
    -- 12 characters, 14 bytes: the row that fails if `bytes` is computed with length()
    or (id = 4 and (lines <> 1 or words <> 2 or bytes <> 14))
