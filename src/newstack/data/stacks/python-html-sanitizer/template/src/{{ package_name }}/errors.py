"""The two failures this tool distinguishes."""


class SanitizeError(ValueError):
    """The input could not be sanitized at all."""


class PolicyError(ValueError):
    """The policy itself is wrong, which is a bug in the caller, not the page."""
