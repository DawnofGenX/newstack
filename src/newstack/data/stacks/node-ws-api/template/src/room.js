// The room owns presence, so a socket never has to know who else is here.
export function createRoom() {
  const members = new Map();

  function presence(event) {
    return { type: "presence", event, clients: members.size };
  }

  return {
    get size() {
      return members.size;
    },
    add(id, socket) {
      members.set(id, socket);
      return presence("join");
    },
    remove(id) {
      members.delete(id);
      return presence("leave");
    },
    broadcast(frame) {
      const payload = JSON.stringify(frame);
      for (const socket of members.values()) {
        if (socket.readyState === socket.OPEN) socket.send(payload);
      }
    },
  };
}
