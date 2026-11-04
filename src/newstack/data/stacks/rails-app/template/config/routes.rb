Rails.application.routes.draw do
  # Health check: 200 while the app boots, 500 otherwise.
  get "up" => "rails/health#show", as: :rails_health_check

  # The one feature this starter ships.
  get "stats" => "stats#show", as: :stats
end
