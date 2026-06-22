import pytest
import requests

MAILPIT_API = "http://localhost:8025/api/v1"


@pytest.fixture
def clear_mailpit():
    try:
        requests.delete(f"{MAILPIT_API}/messages")
    except requests.ConnectionError:
        pytest.skip("Mailpit is not running")


@pytest.fixture
def mailpit_messages(clear_mailpit):
    def _get():
        resp = requests.get(f"{MAILPIT_API}/messages")
        resp.raise_for_status()
        return resp.json()["messages"]

    return _get
