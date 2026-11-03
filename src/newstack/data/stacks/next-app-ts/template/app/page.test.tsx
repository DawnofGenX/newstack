import { afterEach, describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import Page from "./page";

afterEach(() => {
  cleanup();
});

describe("Page", () => {
  it("renders the project title", () => {
    render(<Page />);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toContain(
      "{{ title }}",
    );
  });

  it("increments the counter when the button is clicked", () => {
    render(<Page />);
    const counter = screen.getByTestId("count");
    expect(counter.textContent).toContain("Count: 0");

    fireEvent.click(screen.getByRole("button", { name: "Increment" }));
    expect(screen.getByTestId("count").textContent).toContain("Count: 1");
  });
});
