// The replayable part of the service: what happened, in order, with ids that a
// reconnecting client can quote back as Last-Event-ID.
//
// A bounded log is the whole point. An unbounded one is a memory leak that only
// shows up after a busy afternoon, and an SSE client that reconnects after an
// hour needs *a* recent window, not the entire history.

export class EventLog {
  constructor({ limit = 256 } = {}) {
    if (!Number.isInteger(limit) || limit < 1) {
      throw new RangeError(`limit must be a positive integer, got ${limit}`);
    }
    this.limit = limit;
    this._events = [];
    this._nextId = 1;
  }

  /// Append one event and return it with the id the log assigned.
  append(topic, data) {
    const event = { id: this._nextId, topic, data };
    this._nextId += 1;
    this._events.push(event);
    if (this._events.length > this.limit) {
      this._events.splice(0, this._events.length - this.limit);
    }
    return event;
  }

  /// Everything strictly after `lastId` — the frames a resuming client missed.
  since(lastId) {
    const floor = Number(lastId);
    if (!Number.isFinite(floor)) return [...this._events];
    return this._events.filter((event) => event.id > floor);
  }

  /// The newest id handed out, 0 before the first append.
  get lastId() {
    return this._nextId - 1;
  }

  get size() {
    return this._events.length;
  }
}
