"use client";

import { useEffect, useState } from "react";

import { readCounter, writeCounter } from "./counter-store";

export default function Counter() {
  const [count, setCount] = useState(0);

  // The server has no storage: restore after hydration so markup matches.
  useEffect(() => {
    setCount(readCounter());
  }, []);

  function increment() {
    const next = count + 1;
    setCount(next);
    writeCounter(next);
  }

  return (
    <div className="flex items-center gap-3 rounded-lg border border-black/[.08] px-4 py-3 dark:border-white/[.145]">
      <button
        type="button"
        onClick={increment}
        className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background transition-colors hover:opacity-80"
      >
        Increment
      </button>
      <span role="status" aria-live="polite" data-testid="count" className="text-sm text-zinc-600 dark:text-zinc-400">
        Count: {count}
      </span>
    </div>
  );
}
