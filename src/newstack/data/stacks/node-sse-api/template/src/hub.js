// Who is listening, and what each of them is owed.
//
// The hub holds no HTTP knowledge beyond "write a string to this response", so
// the interesting behaviour (replay, topic filtering, pruning, heartbeat) is
// testable with a fake response object.

import { HEARTBEAT, frame } from "./frame.js";

export const ALL_TOPICS = "*";

export class Hub {
  constructor(log, { heartbeatMs = 15000 } = {}) {
    this.log = log;
    this.heartbeatMs = heartbeatMs;
    /** @type {Map<object, {topic: string}>} */
    this._subs = new Map();
    this._timer = null;
  }

  get size() {
    return this._subs.size;
  }

  /// Register a response and write the frames it missed, if it quoted an id.
  ///
  /// A fresh client (no Last-Event-ID) starts live: replaying the retained
  /// window to somebody who never asked for it would re-show events they have
  /// already seen in another tab.
  subscribe(res, { topic = ALL_TOPICS, lastId = null } = {}) {
    if (lastId !== null && lastId !== undefined && lastId !== "") {
      for (const event of this.log.since(lastId)) {
        if (topic === ALL_TOPICS || event.topic === topic) {
          res.write(frame(event));
        }
      }
    }
    this._subs.set(res, { topic });
    this._ensureHeartbeat();
    return this._subs.size;
  }

  remove(res) {
    this._subs.delete(res);
  }

  /// Append to the log first, then fan out: a subscriber that arrives between
  /// the two must not see the event twice (replay reads the log, delivery reads
  /// the subscriber set).
  publish(topic, data) {
    const event = this.log.append(topic, data);
    const chunk = frame(event);
    for (const [res, sub] of this._subs) {
      if (!this._alive(res)) continue;
      if (sub.topic === ALL_TOPICS || sub.topic === event.topic) {
        res.write(chunk);
      }
    }
    return event;
  }

  close() {
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
    this._subs.clear();
  }

  _alive(res) {
    if (res.writableEnded || res.destroyed) {
      this._subs.delete(res);
      return false;
    }
    return true;
  }

  _ensureHeartbeat() {
    if (this._timer || this.heartbeatMs <= 0) return;
    this._timer = setInterval(() => {
      for (const [res] of this._subs) {
        if (this._alive(res)) res.write(HEARTBEAT);
      }
    }, this.heartbeatMs);
    // Do not hold the event loop open: `npm test` would hang after the last
    // assertion, and a graceful shutdown would wait for the timer.
    this._timer.unref?.();
  }
}
