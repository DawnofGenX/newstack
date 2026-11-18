import pino from "pino";

export function createLogger(options = {}) {
  const level = options.level ?? "info";
  const redact = options.redact ?? ["password", "token", "secret"];
  return pino({
    level,
    redact: { paths: redact, censor: "[REDACTED]" },
    base: { service: options.service ?? "app" },
  });
}

export function childLogger(parent, bindings) {
  return parent.child(bindings ?? {});
}

export function logEvent(logger, level, event, message) {
  logger[level]?.(event, message);
}
