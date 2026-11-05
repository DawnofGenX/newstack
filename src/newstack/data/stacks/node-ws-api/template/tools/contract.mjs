import { WebSocket } from "ws";

const port = process.env.PORT ?? "5453";
const url = `ws://127.0.0.1:${port}/ws`;
let failures = 0;

function check(name, ok, detail = "") {
  if (ok) {
    console.log(`ok ${name}`);
  } else {
    failures += 1;
    console.log(`FAIL ${name}${detail ? ": " + detail : ""}`);
  }
}

function nextFrame(socket) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("no frame within 3s")), 3000);
    socket.once("message", (data) => {
      clearTimeout(timer);
      resolve(JSON.parse(data.toString("utf8")));
    });
  });
}

async function open() {
  const socket = new WebSocket(url);
  const joined = nextFrame(socket);
  await new Promise((resolve, reject) => {
    socket.once("open", resolve);
    socket.once("error", reject);
  });
  return { socket, joined: await joined };
}

const first = await open();
check("first join", JSON.stringify(first.joined) === JSON.stringify({ type: "presence", event: "join", clients: 1 }), JSON.stringify(first.joined));

const second = await open();
const seen = await nextFrame(first.socket);
check("second join", JSON.stringify(second.joined) === JSON.stringify({ type: "presence", event: "join", clients: 2 }), JSON.stringify(second.joined));
check("first hears second", JSON.stringify(seen) === JSON.stringify({ type: "presence", event: "join", clients: 2 }), JSON.stringify(seen));

let answer = nextFrame(first.socket);
first.socket.send(JSON.stringify({ type: "stats", text: "a b\nc\n" }));
check("stats a b/c", JSON.stringify(await answer) === JSON.stringify({ type: "stats", lines: 2, words: 3, bytes: 6 }), "");

answer = nextFrame(second.socket);
second.socket.send(JSON.stringify({ type: "stats", text: "h\u00e9llo w\u00f6rld\n" }));
check("stats utf8", JSON.stringify(await answer) === JSON.stringify({ type: "stats", lines: 1, words: 2, bytes: 14 }), "");

answer = nextFrame(first.socket);
first.socket.send(JSON.stringify({ type: "ping" }));
check("ping", JSON.stringify(await answer) === JSON.stringify({ type: "pong" }), "");

answer = nextFrame(first.socket);
first.socket.send("{");
check("broken json", (await answer).code === "invalid_json", "");

answer = nextFrame(first.socket);
first.socket.send(JSON.stringify({ type: "stats", text: 42 }));
check("non-string text", (await answer).code === "invalid_text", "");

answer = nextFrame(first.socket);
first.socket.send(JSON.stringify({ type: "shout" }));
check("unknown type", (await answer).code === "unknown_type", "");

const leaving = nextFrame(first.socket);
second.socket.close();
check("leave", JSON.stringify(await leaving) === JSON.stringify({ type: "presence", event: "leave", clients: 1 }));

first.socket.close();
console.log(failures === 0 ? "all ws checks passed" : `${failures} ws check(s) failed`);
process.exit(failures === 0 ? 0 : 1);
