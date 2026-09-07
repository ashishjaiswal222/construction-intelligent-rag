class RateLimitException(Exception):
    """Raised when an external API returns a rate limit or quota exceeded error (e.g., HTTP 429)."""
    pass
