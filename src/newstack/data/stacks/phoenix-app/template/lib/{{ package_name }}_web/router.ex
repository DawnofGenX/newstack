defmodule {{ class_name }}Web.Router do
  use {{ class_name }}Web, :router

  pipeline :api do
    plug(:accepts, ["json"])
  end

  scope "/", {{ class_name }}Web do
    pipe_through(:api)

    get("/health", StatController, :health)
    get("/stats", StatController, :show)
    post("/stats", StatController, :create)
  end
end
