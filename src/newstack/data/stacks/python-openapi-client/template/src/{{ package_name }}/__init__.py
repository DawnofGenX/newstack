"""Call an HTTP API through its OpenAPI document, and complain when it disagrees."""

from .client import Client, DriftError, Reply, TransportError
from .spec import Operation, Parameter, Spec, SpecError, load

__version__ = "0.1.0"

__all__ = [
    "Client",
    "DriftError",
    "Operation",
    "Parameter",
    "Reply",
    "Spec",
    "SpecError",
    "TransportError",
    "__version__",
    "load",
]
