import { useState } from "react";

import { readCounter, writeCounter } from "./lib/counter-store";

export default function App() {
  // Lazy initialiser: the stored value is in the first paint, so no flicker to 0.
  const [count, setCount] = useState(readCounter);

  function increment() {
    const next = count + 1;
    setCount(next);
    writeCounter(next);
  }

  return (
    <main className="app">
      <h1>{{ title }}</h1>
      <p role="status" aria-live="polite">Count: {count}</p>
      <button type="button" onClick={increment}>
        Increment
      </button>
    </main>
  );
}
