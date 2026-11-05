import { createServer } from "node:http";
import { WebSocketServer } from "ws";

import { handleFrame } from "./protocol.js";
import { createRoom } from "./room.js";

const MAX_FRAME_BYTES = 64 * 1024;

function sendJson(response, status, payload) {
  const body = Buffer.from(JSON.stringify(payload), "utf8");
  response.writeHead(status, {
    "content-type": "application/json",
    "content-length": String(body.length),
    connection: "close",
  });
  response.end(body);
}

export function createApp() {
  const room = createRoom();
  const sockets = new WebSocketServer({ noServer: true, maxPayload: MAX_FRAME_BYTES });
  let nextId = 1;

  const server = createServer((request, response) => {
    const target = request.url ?? "/";
    const path = target.split("?")[0];
    if (path === "/health") {
      if (request.method !== "GET") {
        sendJson(response, 405, { error: "method_not_allowed", detail: `${request.method} ${path}` });
        return;
      }
      sendJson(response, 200, { status: "ok", clients: room.size });
      return;
    }
    sendJson(response, 404, { error: "not_found", detail: `no route for ${request.method} ${path}` });
  });

  // Only /ws upgrades; every other path goes back to the HTTP router above.
  server.on("upgrade", (request, socket, head) => {
    const path = (request.url ?? "/").split("?")[0];
    if (path !== "/ws") {
      socket.write("HTTP/1.1 404 Not Found\r\nconnection: close\r\n\r\n");
      socket.destroy();
      return;
    }
    sockets.handleUpgrade(request, socket, head, (client) => {
      sockets.emit("connection", client, request);
    });
  });

  sockets.on("connection", (client) => {
    const id = nextId++;
    const joined = room.add(id, client);
    room.broadcast(joined);

    client.on("message", (data, isBinary) => {
      if (isBinary) {
        client.send(
          JSON.stringify({ type: "error", code: "invalid_json", detail: "frames are text" }),
        );
        return;
      }
      const outcome = handleFrame(data.toString("utf8"));
      client.send(JSON.stringify(outcome.frame));
    });

    client.on("close", () => {
      room.broadcast(room.remove(id));
    });
  });

  return { server, sockets, room };
}
