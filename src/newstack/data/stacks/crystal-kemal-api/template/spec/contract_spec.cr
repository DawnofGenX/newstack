require "./spec_helper"

describe {{ class_name }}::Contract do
  it "answers health with 200 and ok" do
    reply = {{ class_name }}::Contract.route("GET", "/health", nil, nil)
    reply.status.should eq 200
    reply.body.to_json.should eq %q({"status":"ok"})
  end

  it "counts the text query parameter" do
    reply = {{ class_name }}::Contract.route("GET", "/stats", "text=hello%20world%0A", nil)
    reply.status.should eq 200
    reply.body["text"].as_s.should eq "hello world\n"
    reply.body["lines"].as_i.should eq 1
    reply.body["words"].as_i.should eq 2
    reply.body["bytes"].as_i.should eq 12
  end

  it "treats a plus as a space in the query string" do
    reply = {{ class_name }}::Contract.route("GET", "/stats", "text=a+b", nil)
    reply.body["text"].as_s.should eq "a b"
    reply.body["words"].as_i.should eq 2
  end

  it "rejects a missing query parameter with 422" do
    reply = {{ class_name }}::Contract.route("GET", "/stats", nil, nil)
    reply.status.should eq 422
    reply.body["error"].as_s.should eq "missing_text"
  end

  it "counts a JSON body" do
    reply = {{ class_name }}::Contract.route("POST", "/stats", nil, %q({"text":"a b\nc\n"}))
    reply.status.should eq 200
    reply.body["lines"].as_i.should eq 2
    reply.body["words"].as_i.should eq 3
    reply.body["bytes"].as_i.should eq 6
  end

  it "keeps padding exactly as sent" do
    reply = {{ class_name }}::Contract.route("POST", "/stats", nil, %q({"text":"  padded  \n"}))
    reply.body["lines"].as_i.should eq 1
    reply.body["words"].should eq 1
    reply.body["bytes"].as_i.should eq 11
  end

  it "rejects a body without text" do
    reply = {{ class_name }}::Contract.route("POST", "/stats", nil, "{}")
    reply.status.should eq 422
    reply.body["error"].as_s.should eq "missing_text"
  end

  it "rejects a non-string text" do
    reply = {{ class_name }}::Contract.route("POST", "/stats", nil, %q({"text":42}))
    reply.status.should eq 422
    reply.body["error"].as_s.should eq "missing_text"
  end

  it "rejects a broken body as invalid JSON" do
    reply = {{ class_name }}::Contract.route("POST", "/stats", nil, "not json")
    reply.status.should eq 422
    reply.body["error"].as_s.should eq "invalid_json"
  end

  it "answers an unknown route with 404" do
    reply = {{ class_name }}::Contract.route("GET", "/nope", nil, nil)
    reply.status.should eq 404
    reply.body["error"].as_s.should eq "not_found"
    reply.body["detail"].as_s.should eq "no route for GET /nope"
  end

  it "answers an unsupported method with 405" do
    reply = {{ class_name }}::Contract.route("DELETE", "/stats", nil, nil)
    reply.status.should eq 405
    reply.body["error"].as_s.should eq "method_not_allowed"
  end
end
