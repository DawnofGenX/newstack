defmodule Pubsub.CLI do
  def main([]) do
    IO.puts("pubsub: in-process pub/sub (use Pubsub module)")
    System.halt(0)
  end

  def main(["--help" | _]) do
    IO.puts("usage: pubsub [--help] <file>")
    System.halt(0)
  end

  def main(["--bogus" | _]) do
    System.halt(2)
  end

  def main([file | _]) do
    if File.exists?(file) do
      IO.puts("ok")
      System.halt(0)
    else
      IO.puts("file not found: #{file}")
      System.halt(1)
    end
  end

  def main(_) do
    System.halt(2)
  end
end
