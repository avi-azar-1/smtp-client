import smtplib
import time
from types import TracebackType
from typing import Self

from .email import Email
from .exceptions import ConnectionError, SendError


class SmtpClient:

    def __init__(
        self,
        host: str,
        port: int,
        *,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._connection: smtplib.SMTP | None = None

    def send(self, email: Email) -> None:
        msg = email.build()
        raw = msg.as_string()
        recipients = email.all_recipients()

        for attempt in range(self.max_retries):
            try:
                conn = self._connection or self._connect()
                conn.sendmail(email.from_addr, recipients, raw)
                if self._connection is None:
                    conn.quit()
                return
            except (OSError, smtplib.SMTPServerDisconnected) as exc:
                self._connection = None
                if attempt == self.max_retries - 1:
                    raise ConnectionError(
                        f"Failed to send after {self.max_retries} attempts: {exc}"
                    ) from exc
                time.sleep(self.retry_delay * (2**attempt))
            except smtplib.SMTPRecipientsRefused as exc:
                raise SendError(f"Recipients refused: {exc}") from exc
            except smtplib.SMTPException as exc:
                raise SendError(f"SMTP error: {exc}") from exc

    def _connect(self) -> smtplib.SMTP:
        return smtplib.SMTP(self.host, self.port, timeout=self.timeout)

    def _disconnect(self) -> None:
        if self._connection is not None:
            try:
                self._connection.quit()
            except (OSError, smtplib.SMTPException):
                pass
            self._connection = None

    def __enter__(self) -> Self:
        try:
            self._connection = self._connect()
        except (OSError, smtplib.SMTPConnectError) as exc:
            raise ConnectionError(
                f"Cannot connect to {self.host}:{self.port}: {exc}"
            ) from exc
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._disconnect()
