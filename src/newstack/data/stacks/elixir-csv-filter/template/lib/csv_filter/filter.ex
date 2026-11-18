defmodule CsvFilter.Filter do
  @moduledoc "Filters CSV rows by a column value."

  @spec filter(binary(), String.t(), String.t(), boolean(), boolean()) :: binary()
  def filter(data, column, value, invert \\ false, header \\ true) do
    lines = String.split(data, "\n")

    {body, trailing} =
      if List.last(lines) == "" do
        {Enum.drop(lines, -1), "\n"}
      else
        {lines, ""}
      end

    case body do
      [] ->
        trailing

      [first | rest] when header ->
        idx = resolve_column(first, column)

        kept =
          Enum.filter(rest, fn row ->
            matches?(row, idx, value) != invert
          end)

        Enum.join([first | kept], "\n") <> trailing

      rows ->
        idx = resolve_column(nil, column, rows)

        kept =
          Enum.filter(rows, fn row ->
            matches?(row, idx, value) != invert
          end)

        Enum.join(kept, "\n") <> trailing
    end
  end

  defp resolve_column(header, column) do
    case Integer.parse(column) do
      {n, ""} when n > 0 ->
        n - 1

      _ when is_binary(header) ->
        header
        |> String.split(",")
        |> Enum.map(&String.trim/1)
        |> Enum.find_index(&(&1 == String.trim(column)))
        |> case do
          nil -> 0
          i -> i
        end

      _ ->
        0
    end
  end

  defp resolve_column(nil, column, _rows) do
    case Integer.parse(column) do
      {n, ""} when n > 0 -> n - 1
      _ -> 0
    end
  end

  defp matches?(row, idx, value) do
    cells = String.split(row, ",")
    cell = Enum.at(cells, idx, "") |> String.trim()
    cell == value
  end
end
