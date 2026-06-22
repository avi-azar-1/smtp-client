import time
from unittest.mock import patch

import pytest

from smtp_client import ConnectionError, Email, SmtpClient

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    return SmtpClient("localhost", 1025, max_retries=2, retry_delay=0.1)


@pytest.fixture
def sample_email():
    return Email(
        from_addr="test@example.com",
        to=["recipient@example.com"],
        subject="Test Email",
        text="Hello from tests",
    )


class TestSendEmail:

    def test_send_text(self, client, sample_email, mailpit_messages):
        client.send(sample_email)
        messages = mailpit_messages()
        assert len(messages) == 1
        assert messages[0]["Subject"] == "Test Email"

    def test_send_html(self, client, mailpit_messages):
        email = Email(
            from_addr="test@example.com",
            to=["recipient@example.com"],
            subject="HTML Test",
            html="<h1>Hello</h1>",
        )
        client.send(email)
        messages = mailpit_messages()
        assert len(messages) == 1
        assert messages[0]["Subject"] == "HTML Test"

    def test_send_with_cc(self, client, mailpit_messages):
        email = Email(
            from_addr="test@example.com",
            to=["a@example.com"],
            cc=["b@example.com"],
            subject="CC Test",
            text="body",
        )
        client.send(email)
        messages = mailpit_messages()
        assert len(messages) == 1

    def test_send_with_attachment(self, client, mailpit_messages, tmp_path):
        file = tmp_path / "report.txt"
        file.write_text("report data")

        email = Email(
            from_addr="test@example.com",
            to=["recipient@example.com"],
            subject="Attachment Test",
            text="See attached",
        )
        email.attach(file)
        client.send(email)
        messages = mailpit_messages()
        assert len(messages) == 1
        assert messages[0]["Attachments"] > 0


class TestContextManager:

    def test_multiple_sends(self, mailpit_messages):
        with SmtpClient("localhost", 1025) as client:
            for i in range(3):
                email = Email(
                    from_addr="test@example.com",
                    to=["recipient@example.com"],
                    subject=f"Message {i}",
                    text=f"Body {i}",
                )
                client.send(email)

        messages = mailpit_messages()
        assert len(messages) == 3


class TestRetryAndErrors:

    def test_connection_refused(self):
        client = SmtpClient("localhost", 9999, max_retries=2, retry_delay=0.01)
        email = Email(
            from_addr="test@example.com",
            to=["recipient@example.com"],
            subject="Will fail",
            text="body",
        )
        with pytest.raises(ConnectionError):
            client.send(email)

    def test_retry_backoff(self):
        client = SmtpClient("localhost", 9999, max_retries=3, retry_delay=0.5)
        email = Email(
            from_addr="test@example.com",
            to=["recipient@example.com"],
            subject="Will fail",
            text="body",
        )
        with patch("smtp_client.client.time.sleep") as mock_sleep:
            with pytest.raises(ConnectionError):
                client.send(email)
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(0.5)
            mock_sleep.assert_any_call(1.0)
