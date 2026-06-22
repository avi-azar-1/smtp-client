import re
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Self

from .exceptions import ValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Email:

    def __init__(
        self,
        *,
        from_addr: str,
        to: list[str],
        subject: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        text: str | None = None,
        html: str | None = None,
    ) -> None:
        self.from_addr = from_addr
        self.to = to
        self.cc = cc or []
        self.bcc = bcc or []
        self.subject = subject
        self.text = text
        self.html = html
        self._attachments: list[Path] = []

    def attach(self, file_path: str | Path) -> Self:
        path = Path(file_path)
        if not path.is_file():
            raise ValidationError(f"Attachment not found: {path}")
        self._attachments.append(path)
        return self

    def all_recipients(self) -> list[str]:
        return self.to + self.cc + self.bcc

    def build(self) -> MIMEMultipart:
        self._validate()

        msg = MIMEMultipart("mixed")
        msg["From"] = self.from_addr
        msg["To"] = ", ".join(self.to)
        if self.cc:
            msg["Cc"] = ", ".join(self.cc)
        msg["Subject"] = self.subject

        if self.text and self.html:
            alt = MIMEMultipart("alternative")
            alt.attach(MIMEText(self.text, "plain"))
            alt.attach(MIMEText(self.html, "html"))
            msg.attach(alt)
        elif self.text:
            msg.attach(MIMEText(self.text, "plain"))
        elif self.html:
            msg.attach(MIMEText(self.html, "html"))

        for path in self._attachments:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(path.read_bytes())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", "attachment", filename=path.name
            )
            msg.attach(part)

        return msg

    def _validate(self) -> None:
        if not self.from_addr:
            raise ValidationError("from_addr is required")
        if not _EMAIL_RE.match(self.from_addr):
            raise ValidationError(f"Invalid from address: {self.from_addr}")

        recipients = self.all_recipients()
        if not recipients:
            raise ValidationError("At least one recipient is required")
        for addr in recipients:
            if not _EMAIL_RE.match(addr):
                raise ValidationError(f"Invalid recipient address: {addr}")

        if not self.text and not self.html:
            raise ValidationError("At least one of text or html body is required")
