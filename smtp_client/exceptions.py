class SmtpClientError(Exception):
    """Base exception for smtp_client package."""


class ConnectionError(SmtpClientError):
    """Raised when the SMTP server is unreachable."""


class SendError(SmtpClientError):
    """Raised when the server rejects the message."""


class ValidationError(SmtpClientError):
    """Raised when email construction is invalid."""
