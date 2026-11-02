import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import App from "./App";

afterEach(cleanup);

describe("App", () => {
  it("renders the project heading", () => {
    render(<App />);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toContain("{{ title }}");
  });

  it("increments the counter", () => {
    render(<App />);
    expect(screen.getByText("Count: 0")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /increment/i }));
    expect(screen.getByText("Count: 1")).toBeTruthy();
  });
});
