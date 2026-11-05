-- `wc` semantics, expressed in SQL: a line is a chr(10), a word is a run of non-whitespace,
-- and bytes are UTF-8 bytes (`length` counts characters, `strlen` counts bytes in DuckDB —
-- the one place the two disagree is exactly where they should).
with texts as (

    select
        id,
        title,
        text
    from {{ ref('stg_documents') }}

)

select
    id,
    title,
    text,
    length(text) - length(replace(text, chr(10), '')) as lines,
    len(regexp_extract_all(text, '\S+')) as words,
    strlen(text) as bytes
from texts
