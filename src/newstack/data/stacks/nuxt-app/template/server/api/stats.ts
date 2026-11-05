import { stats } from "../../lib/counts";

// One file, every method: a `stats.get.ts` leaves POST to the page renderer,
// which answers 200 with HTML instead of a 405.
export default defineEventHandler((event) => {
  if (event.method !== "GET") {
    setResponseHeader(event, "allow", "GET");
    setResponseStatus(event, 405);
    return {
      error: "method_not_allowed",
      detail: `${event.method} is not allowed on /api/stats`,
    };
  }
  const text = getQuery(event).text;
  if (typeof text !== "string") {
    setResponseStatus(event, 422);
    return { error: "missing_text", detail: "pass ?text=" };
  }
  return stats(text);
});
