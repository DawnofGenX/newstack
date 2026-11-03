defmodule Textstat.Counts do
  @moduledoc """
  Line, word and byte totals for one input.

  A plain struct so tests compare values directly; nothing here touches a device.
  """

  @enforce_keys [:lines, :words, :bytes]
  defstruct [:lines, :words, :bytes]

  @type t :: %__MODULE__{
          lines: non_neg_integer(),
          words: non_neg_integer(),
          bytes: non_neg_integer()
        }

  @spec new(non_neg_integer(), non_neg_integer(), non_neg_integer()) :: t()
  def new(lines, words, bytes) when lines >= 0 and words >= 0 and bytes >= 0 do
    %__MODULE__{lines: lines, words: words, bytes: bytes}
  end

  @spec plus(t(), t()) :: t()
  def plus(%__MODULE__{} = left, %__MODULE__{} = right) do
    new(left.lines + right.lines, left.words + right.words, left.bytes + right.bytes)
  end
end
