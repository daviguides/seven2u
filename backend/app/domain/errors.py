"""Domain exceptions mapped to HTTP responses at the API edge."""


class DomainError(Exception):
    """Base class for all domain errors."""


class NotFoundError(DomainError):
    """A requested entity does not exist."""


class ValidationError(DomainError):
    """Input violates a domain invariant."""


class UpstreamError(DomainError):
    """An external dependency (TVMaze) failed."""
