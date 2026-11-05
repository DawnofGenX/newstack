require "./server"

port = ENV.fetch("PORT", "8080").to_i
{{ class_name }}.start(port)
