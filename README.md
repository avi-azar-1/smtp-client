# smtp-client

A lightweight Python SMTP client for sending emails with no authentication. Built on stdlib `smtplib` — zero runtime dependencies.

## Requirements

- Python 3.12+

## Installation

```bash
pip install -e .
```

## Usage

### Basic send

```python
from smtp_client import Email, SmtpClient

email = Email(
    from_addr="app@example.com",
    to=["user@example.com"],
    subject="Hello",
    text="Plain text body",
)

client = SmtpClient("localhost", 1025)
client.send(email)
```

### HTML email

```python
email = Email(
    from_addr="app@example.com",
    to=["user@example.com"],
    subject="Welcome",
    text="Fallback plain text",
    html="<h1>Welcome!</h1><p>Great to have you.</p>",
)
```

When both `text` and `html` are provided, the message is sent as `multipart/alternative` so mail clients can render the appropriate format.

### Attachments

```python
email = Email(
    from_addr="app@example.com",
    to=["user@example.com"],
    subject="Invoice Ready",
    text="Please find your invoice attached.",
)
email.attach("invoice.pdf").attach("receipt.pdf")  # fluent chaining
```

### CC and BCC

```python
email = Email(
    from_addr="app@example.com",
    to=["user@example.com"],
    cc=["manager@example.com"],
    bcc=["audit@example.com"],
    subject="Quarterly Report",
    text="See attached.",
)
```

BCC recipients are included in the SMTP envelope but not exposed in message headers.

### Sending multiple emails (connection reuse)

Use the context manager to hold a persistent connection across multiple sends:

```python
emails = [...]

with SmtpClient("localhost", 1025) as client:
    for email in emails:
        client.send(email)
```

## API Reference

### `Email`

```python
Email(
    *,
    from_addr: str,
    to: list[str],
    subject: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    text: str | None = None,
    html: str | None = None,
)
```

| Parameter   | Required | Description                          |
|-------------|----------|--------------------------------------|
| `from_addr` | Yes      | Sender address                       |
| `to`        | Yes      | List of recipient addresses          |
| `subject`   | Yes      | Email subject line                   |
| `cc`        | No       | CC recipients (appear in headers)    |
| `bcc`       | No       | BCC recipients (envelope only)       |
| `text`      | No*      | Plain text body                      |
| `html`      | No*      | HTML body                            |

*At least one of `text` or `html` is required.

#### Methods

- **`.attach(file_path: str | Path) -> Email`** — add a file attachment; returns `self` for chaining
- **`.build() -> MIMEMultipart`** — validate and assemble the MIME message
- **`.all_recipients() -> list[str]`** — returns `to + cc + bcc`

### `SmtpClient`

```python
SmtpClient(
    host: str,
    port: int,
    *,
    timeout: float = 30.0,
    max_retries: int = 3,
    retry_delay: float = 1.0,
)
```

| Parameter     | Default | Description                                          |
|---------------|---------|------------------------------------------------------|
| `host`        | —       | SMTP server hostname                                 |
| `port`        | —       | SMTP server port                                     |
| `timeout`     | `30.0`  | Connection timeout in seconds                        |
| `max_retries` | `3`     | Max attempts on transient failures                   |
| `retry_delay` | `1.0`   | Base delay in seconds (doubles each retry)           |

#### Methods

- **`.send(email: Email)`** — build and send the email; retries on transient network errors
- **`__enter__` / `__exit__`** — context manager for persistent connection reuse

### Exceptions

All exceptions inherit from `SmtpClientError`.

| Exception         | Raised when                                        |
|-------------------|----------------------------------------------------|
| `ValidationError` | Email is missing required fields or has bad addresses |
| `ConnectionError` | SMTP server is unreachable after all retries       |
| `SendError`       | Server accepted the connection but rejected the message |

```python
from smtp_client import SmtpClient, Email, ConnectionError, SendError, ValidationError

try:
    client.send(email)
except ValidationError as e:
    print(f"Bad email: {e}")
except ConnectionError as e:
    print(f"Server unreachable: {e}")
except SendError as e:
    print(f"Server rejected message: {e}")
```

> **Note:** `smtp_client.ConnectionError` shadows Python's built-in `ConnectionError`. Import explicitly from `smtp_client` to avoid ambiguity.

## Testing

Unit tests run without any external services:

```bash
pip install -e ".[dev]"
pytest tests/test_email.py -v
```

Integration tests require [Mailpit](https://github.com/axllent/mailpit) running locally. Start it with Docker:

```bash
docker compose up -d
pytest tests/test_client.py -v -m integration
docker compose down
```

Mailpit web UI is available at **http://localhost:8025** — inspect captured emails in the browser.

To run only unit tests (skip integration):

```bash
pytest -m "not integration"
```
