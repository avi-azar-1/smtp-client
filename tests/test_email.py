import tempfile
from pathlib import Path

import pytest

from smtp_client import Email, ValidationError


class TestEmailBuild:

    def test_text_only(self):
        email = Email(
            from_addr="sender@example.com",
            to=["recipient@example.com"],
            subject="Hello",
            text="Plain text body",
        )
        msg = email.build()
        assert msg["From"] == "sender@example.com"
        assert msg["To"] == "recipient@example.com"
        assert msg["Subject"] == "Hello"
        payload = msg.get_payload()
        assert any("Plain text body" in p.get_payload() for p in payload if hasattr(p, "get_payload"))

    def test_html_only(self):
        email = Email(
            from_addr="sender@example.com",
            to=["recipient@example.com"],
            subject="Hello",
            html="<p>HTML body</p>",
        )
        msg = email.build()
        payload = msg.get_payload()
        assert any("<p>HTML body</p>" in p.get_payload() for p in payload if hasattr(p, "get_payload"))

    def test_text_and_html(self):
        email = Email(
            from_addr="sender@example.com",
            to=["recipient@example.com"],
            subject="Hello",
            text="Plain",
            html="<p>HTML</p>",
        )
        msg = email.build()
        alt_part = msg.get_payload()[0]
        assert alt_part.get_content_type() == "multipart/alternative"
        parts = alt_part.get_payload()
        assert parts[0].get_content_type() == "text/plain"
        assert parts[1].get_content_type() == "text/html"

    def test_cc_in_headers_bcc_not(self):
        email = Email(
            from_addr="sender@example.com",
            to=["a@example.com"],
            cc=["b@example.com"],
            bcc=["c@example.com"],
            subject="Test",
            text="body",
        )
        msg = email.build()
        assert msg["Cc"] == "b@example.com"
        assert msg["Bcc"] is None

    def test_all_recipients(self):
        email = Email(
            from_addr="sender@example.com",
            to=["a@example.com"],
            cc=["b@example.com"],
            bcc=["c@example.com"],
            subject="Test",
            text="body",
        )
        assert email.all_recipients() == [
            "a@example.com",
            "b@example.com",
            "c@example.com",
        ]

    def test_attachment(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"file content")
            path = Path(f.name)

        try:
            email = Email(
                from_addr="sender@example.com",
                to=["recipient@example.com"],
                subject="With attachment",
                text="See attached",
            )
            email.attach(path)
            msg = email.build()
            parts = msg.get_payload()
            attachment_part = parts[-1]
            assert attachment_part.get_filename() == path.name
        finally:
            path.unlink()

    def test_fluent_attach(self):
        with tempfile.NamedTemporaryFile(suffix=".a", delete=False) as f1:
            f1.write(b"a")
            p1 = Path(f1.name)
        with tempfile.NamedTemporaryFile(suffix=".b", delete=False) as f2:
            f2.write(b"b")
            p2 = Path(f2.name)

        try:
            email = Email(
                from_addr="sender@example.com",
                to=["recipient@example.com"],
                subject="Multi",
                text="body",
            )
            result = email.attach(p1).attach(p2)
            assert result is email
            msg = email.build()
            filenames = [p.get_filename() for p in msg.get_payload() if p.get_filename()]
            assert p1.name in filenames
            assert p2.name in filenames
        finally:
            p1.unlink()
            p2.unlink()


class TestEmailValidation:

    def test_no_from_addr(self):
        with pytest.raises(ValidationError, match="from_addr"):
            Email(
                from_addr="",
                to=["a@example.com"],
                subject="Test",
                text="body",
            ).build()

    def test_invalid_from_addr(self):
        with pytest.raises(ValidationError, match="Invalid from"):
            Email(
                from_addr="not-an-email",
                to=["a@example.com"],
                subject="Test",
                text="body",
            ).build()

    def test_no_recipients(self):
        with pytest.raises(ValidationError, match="recipient"):
            Email(
                from_addr="sender@example.com",
                to=[],
                subject="Test",
                text="body",
            ).build()

    def test_invalid_recipient(self):
        with pytest.raises(ValidationError, match="Invalid recipient"):
            Email(
                from_addr="sender@example.com",
                to=["bad-address"],
                subject="Test",
                text="body",
            ).build()

    def test_no_body(self):
        with pytest.raises(ValidationError, match="body"):
            Email(
                from_addr="sender@example.com",
                to=["a@example.com"],
                subject="Test",
            ).build()

    def test_attachment_not_found(self):
        email = Email(
            from_addr="sender@example.com",
            to=["a@example.com"],
            subject="Test",
            text="body",
        )
        with pytest.raises(ValidationError, match="not found"):
            email.attach("/nonexistent/file.txt")
