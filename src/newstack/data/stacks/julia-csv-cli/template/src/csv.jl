"""
    CsvError(message)

Raised for malformed CSV. Every message starts with the 1-based line number, so
a user can find the offending row.
"""
struct CsvError <: Exception
    message::String
end

Base.showerror(io::IO, error::CsvError) = print(io, error.message)

"""
    CsvTable(headers, rows)

A parsed document: the first record is the header, the rest are data rows that
all have the same width.
"""
struct CsvTable
    headers::Vector{String}
    rows::Vector{Vector{String}}
end

function Base.:(==)(left::CsvTable, right::CsvTable)
    return left.headers == right.headers && left.rows == right.rows
end

_nfields(row::Vector{String}) = length(row)

"""
    parse_csv(text; delimiter = ',') -> CsvTable

Reads RFC 4180 CSV: quoted fields may hold the delimiter, doubled quotes and
newlines; CRLF outside quotes is accepted.
"""
function parse_csv(text::AbstractString; delimiter::Char=',')
    delimiter in ('"', '\r', '\n') && throw(CsvError("the delimiter must not be a quote or a newline"))

    records = Vector{Vector{String}}()
    field = IOBuffer()
    row = String[]
    quoted = false
    line = 1
    quoted_at = 0
    index = firstindex(text)

    while index <= lastindex(text)
        char = text[index]
        if quoted
            if char == '"'
                following = index < lastindex(text) ? text[nextind(text, index)] : '\0'
                if following == '"'
                    print(field, '"')
                    index = nextind(text, index)
                else
                    quoted = false
                end
            else
                char == '\n' && (line += 1)
                print(field, char)
            end
        elseif char == '"'
            stripped = String(take!(field))
            isempty(stripped) || throw(CsvError("line $line: text before a quoted field"))
            quoted = true
            quoted_at = line
        elseif char == delimiter
            push!(row, String(take!(field)))
        elseif char == '\n' || (char == '\r' && index < lastindex(text) && text[nextind(text, index)] == '\n')
            push!(row, String(take!(field)))
            push!(records, row)
            row = String[]
            if char == '\r'
                index = nextind(text, index)
            end
            line += 1
        elseif char == '\r'
            throw(CsvError("line $line: bare carriage return"))
        else
            print(field, char)
        end
        index = nextind(text, index)
    end

    quoted && throw(CsvError("line $quoted_at: unterminated quoted field"))
    if field.size > 0 || !isempty(row)
        push!(row, String(take!(field)))
        push!(records, row)
    end

    isempty(records) && throw(CsvError("the document is empty"))
    headers = records[1]
    width = length(headers)
    rows = records[2:end]
    for (offset, record) in enumerate(rows)
        length(record) == width || throw(CsvError("line $(offset + 1): $(length(record)) fields, expected $width"))
    end
    return CsvTable(headers, rows)
end

"""
    _quote(field, delimiter) -> String

Quotes a field only when it has to be quoted.
"""
function _quote(field::AbstractString, delimiter::Char)
    needs = any(char -> char == delimiter || char == '"' || char == '\n' || char == '\r', field) ||
            (startswith(field, " ") || endswith(field, " "))
    needs || return String(field)
    return string('"', replace(field, '"' => "\"\""), '"')
end

"""
    render_csv(table; delimiter = ',') -> String

Writes the table back out with minimal quoting and a trailing newline per row.
"""
function render_csv(table::CsvTable; delimiter::Char=',')
    io = IOBuffer()
    println(io, join((_quote(header, delimiter) for header in table.headers), delimiter))
    for row in table.rows
        println(io, join((_quote(field, delimiter) for field in row), delimiter))
    end
    return String(take!(io))
end

"""
    column_index(table, spec) -> Int

Resolves a column name or a 1-based position to an index, or throws.
"""
function column_index(table::CsvTable, spec::AbstractString)
    position = tryparse(Int, spec)
    if position !== nothing
        (1 <= position <= length(table.headers)) ||
            throw(CsvError("column $position is out of range: the table has $(length(table.headers))"))
        return position
    end
    found = findfirst(==(spec), table.headers)
    found === nothing && throw(CsvError("unknown column '$spec'"))
    return found
end

"""
    select_columns(table, specs) -> CsvTable

Keeps the named columns, in the order given, dropping everything else.
"""
function select_columns(table::CsvTable, specs::Vector{String})
    isempty(specs) && return table
    indices = [column_index(table, spec) for spec in specs]
    return CsvTable(
        [table.headers[index] for index in indices],
        [[row[index] for index in indices] for row in table.rows],
    )
end

"""
    column_summary(table, spec) -> Vector{Pair{String,Any}}

Statistics for one column: count, numeric count, sum, mean, min and max. A
column with no numbers reports only the count.
"""
function column_summary(table::CsvTable, spec::AbstractString)
    index = column_index(table, spec)
    values = [row[index] for row in table.rows]
    numbers = [value for value in (tryparse(Float64, strip(value)) for value in values) if value !== nothing]
    result = Pair{String,Any}["column" => table.headers[index], "count" => length(values)]
    if !isempty(numbers)
        push!(result, "numbers" => length(numbers))
        push!(result, "sum" => sum(numbers))
        push!(result, "mean" => sum(numbers) / length(numbers))
        push!(result, "min" => minimum(numbers))
        push!(result, "max" => maximum(numbers))
    end
    return result
end

_escape(text::AbstractString) = replace(String(text), '"' => "\\\"", '\\' => "\\\\",
                                       '\n' => "\\n", '\t' => "\\t", '\r' => "\\r")

"""
    to_json(table) -> String

Renders the table as an array of objects, keys in header order.
"""
function to_json(table::CsvTable)
    io = IOBuffer()
    print(io, "[")
    for (offset, row) in enumerate(table.rows)
        offset > 1 && print(io, ",")
        print(io, "{")
        for (position, header) in enumerate(table.headers)
            position > 1 && print(io, ",")
            print(io, '"', _escape(header), "\":\"", _escape(row[position]), '"')
        end
        print(io, "}")
    end
    print(io, "]")
    return String(take!(io))
end
