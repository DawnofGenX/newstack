local socket = require("socket")
local contract = require("contract")

local M = {}

local function read_request(client)
  local head = {}
  local length = 0
  while true do
    local chunk, err, partial = client:receive(1)
    if not chunk then
      return nil, err or partial
    end
    head[#head + 1] = chunk
    length = length + 1
    local tail = table.concat(head)
    if #tail >= 4 and tail:sub(-4) == "\r\n\r\n" then
      break
    end
    if length > 8192 then
      return nil, "request head too large"
    end
  end
  local text = table.concat(head)
  local request_line, header_block = text:match("^(.-)\r\n(.*)\r\n\r\n$")
  if not request_line then
    return nil, "malformed request"
  end
  local method, target = request_line:match("^(%u+) (%S+) ")
  if not method then
    return nil, "malformed request line"
  end

  local headers = {}
  for line in (header_block .. "\r\n"):gmatch("(.-)\r\n") do
    local name, value = line:match("^([^:]+):%s*(.-)%s*$")
    if name then
      headers[name:lower()] = value
    end
  end

  local body = ""
  local declared = tonumber(headers["content-length"] or "0") or 0
  if declared > 0 then
    local chunk = client:receive(declared)
    if not chunk then
      return nil, "body shorter than Content-Length"
    end
    body = chunk
  end

  local path, query = target:match("^([^?]*)%??(.*)$")
  return { method = method, path = path, query = query or "", body = body }
end

local function respond(client, status, body)
  local reason = ({
    [200] = "OK",
    [404] = "Not Found",
    [405] = "Method Not Allowed",
    [422] = "Unprocessable Entity",
  })[status] or "Internal Server Error"
  local response = table.concat({
    string.format("HTTP/1.1 %d %s", status, reason),
    "content-type: application/json",
    string.format("content-length: %d", #body),
    "connection: close",
    "",
    body,
  }, "\r\n")
  client:send(response)
end

function M.serve(host, port)
  local server = assert(socket.bind(host, port))
  while true do
    local client = server:accept()
    if client then
      client:settimeout(5)
      local request, err = read_request(client)
      if request then
        local reply = contract.route(request.method, request.path, request.query, request.body)
        respond(client, reply.status, reply.body)
      else
        respond(client, 422, string.format('{"error":"invalid_json","detail":"%s"}', err or "bad request"))
      end
      client:close()
    end
  end
end

return M
