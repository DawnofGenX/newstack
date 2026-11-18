defmodule Pubsub do
  @moduledoc """
  In-process pub/sub built on a GenServer.
  """

  def start_link(opts \\ []) do
    Pubsub.Server.start_link(opts)
  end

  def subscribe(topic, handler) do
    Pubsub.Server.subscribe(topic, handler)
  end

  def subscribe(server, topic, handler) do
    Pubsub.Server.subscribe(server, topic, handler)
  end

  def unsubscribe(topic, handler) do
    Pubsub.Server.unsubscribe(topic, handler)
  end

  def publish(topic, message) do
    Pubsub.Server.publish(topic, message)
  end

  def publish(server, topic, message) do
    Pubsub.Server.publish(server, topic, message)
  end

  def topics do
    Pubsub.Server.topics()
  end
end
