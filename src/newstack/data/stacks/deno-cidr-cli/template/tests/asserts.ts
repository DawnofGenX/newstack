/** Minimal assertions so the suite needs no remote imports. */
export function assertEquals(actual: unknown, expected: unknown, message = ""): void {
  const left = JSON.stringify(actual);
  const right = JSON.stringify(expected);
  if (left !== right) {
    throw new Error(`${message ? message + ": " : ""}expected ${right}, got ${left}`);
  }
}

export function assertThrows(
  body: () => unknown,
  errorType: new (...args: any[]) => Error,
): void {
  try {
    body();
  } catch (error) {
    if (error instanceof errorType) {
      return;
    }
    throw new Error(`expected ${errorType.name}, got ${(error as Error).name}`);
  }
  throw new Error(`expected ${errorType.name}, nothing was thrown`);
}
