import { countText } from "./lib/counts.mjs";

const input = document.querySelector("[data-testid='input']");
const lines = document.querySelector("[data-testid='lines']");
const words = document.querySelector("[data-testid='words']");
const bytes = document.querySelector("[data-testid='bytes']");
const summary = document.querySelector("[data-testid='summary']");

function render() {
  const counts = countText(input.value);
  lines.textContent = String(counts.lines);
  words.textContent = String(counts.words);
  bytes.textContent = String(counts.bytes);
  const plural = (n, noun) => `${n} ${noun}${n === 1 ? "" : "s"}`;
  summary.textContent = [plural(counts.lines, "line"), plural(counts.words, "word"), plural(counts.bytes, "byte")].join(" \u00b7 ");
}

input.addEventListener("input", render);
document.querySelector("[data-testid='clear']").addEventListener("click", () => {
  input.value = "";
  render();
});

document.querySelector("[data-testid='ask-server']").addEventListener("click", async () => {
  const answer = document.querySelector("[data-testid='server-answer']");
  answer.textContent = "asking…";
  const response = await fetch(`/api/stats?text=${encodeURIComponent(input.value)}`);
  const body = await response.json();
  answer.textContent = `server saw ${body.lines}/${body.words}/${body.bytes}`;
});

render();
