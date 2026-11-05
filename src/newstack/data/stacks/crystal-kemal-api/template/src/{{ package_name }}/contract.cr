require "json"
require "uri"

require "./counts"

module {{ class_name }}
  # One HTTP answer: the status code and the JSON document.
  record Reply, status : Int32, body : JSON::Any

  # The whole service contract as a pure function — no sockets, so `crystal spec`
  # covers every status code and body without opening a port.
  module Contract
    def self.counts_json(text : String, counts : Counts) : JSON::Any
      JSON.parse({"text" => text.as(String?), "lines" => counts.lines, "words" => counts.words, "bytes" => counts.bytes}.to_json)
    end

    def self.error(status : Int32, code : String, detail : String? = nil) : Reply
      payload = {} of String => String?
      payload["error"] = code
      payload["detail"] = detail
      Reply.new(status, JSON.parse(payload.to_json))
    end

    def self.route(method : String, path : String, query : String?, body : String?) : Reply
      case path
      when "/health"
        return error(405, "method_not_allowed") unless method == "GET"
        Reply.new(200, JSON.parse(%({"status":"ok"})))
      when "/stats"
        case method
        when "GET"
          params = URI::Params.parse(query || "")
          text = params["text"]?
          return error(422, "missing_text", "the `text` query parameter is required") if text.nil?
          Reply.new(200, counts_json(text, {{ class_name }}.count_text(text)))
        when "POST"
          payload =
            begin
              parsed = JSON.parse(body || "")
              parsed.as_h?
            rescue JSON::ParseException
              nil
            end
          return error(422, "invalid_json", "the request body must be a JSON object") if payload.nil?
          text = payload["text"]?.try(&.as_s?)
          return error(422, "missing_text", "`text` must be a string") if text.nil?
          Reply.new(200, counts_json(text, {{ class_name }}.count_text(text)))
        else
          error(405, "method_not_allowed")
        end
      else
        error(404, "not_found", "no route for #{method} #{path}")
      end
    end
  end
end
