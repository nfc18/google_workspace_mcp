"""
Pytest configuration and shared fixtures.

SECURITY NOTE:
- All test data uses generic @test.example.com addresses
- No real credentials, API keys, or personal data
- No real Gmail message IDs or thread IDs
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import base64

# =============================================================================
# SECURITY: Generic test constants - NO real data
# =============================================================================

TEST_USER_EMAIL = "test-user@test.example.com"
TEST_SENDER_EMAIL = "sender@test.example.com"
TEST_RECIPIENT_EMAIL = "recipient@test.example.com"
TEST_CC_EMAIL = "cc-user@test.example.com"
TEST_MESSAGE_ID_HEADER = "<test-msg-001@mail.test.example.com>"
TEST_THREAD_ID = "thread-test-abc123"
TEST_MSG_ID = "msg-test-001"
TEST_DRAFT_ID = "draft-test-001"


# =============================================================================
# Gmail API Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_gmail_service():
    """
    Mock Gmail API service.

    Returns a MagicMock that simulates the Gmail API service object.
    No real API calls are made.
    """
    service = MagicMock()

    # Chain the API call pattern: service.users().messages().get()
    users_mock = MagicMock()
    service.users.return_value = users_mock

    messages_mock = MagicMock()
    users_mock.messages.return_value = messages_mock

    drafts_mock = MagicMock()
    users_mock.drafts.return_value = drafts_mock

    return service


@pytest.fixture
def sample_message_response():
    """
    Sample Gmail API message response.

    SECURITY: Uses only generic test data.
    """
    return {
        "id": TEST_MSG_ID,
        "threadId": TEST_THREAD_ID,
        "labelIds": ["INBOX"],
        "snippet": "This is a test message snippet...",
        "payload": {
            "partId": "",
            "mimeType": "text/plain",
            "headers": [
                {"name": "Subject", "value": "Test Subject"},
                {"name": "From", "value": f"Test Sender <{TEST_SENDER_EMAIL}>"},
                {"name": "To", "value": TEST_RECIPIENT_EMAIL},
                {"name": "Cc", "value": TEST_CC_EMAIL},
                {"name": "Message-ID", "value": TEST_MESSAGE_ID_HEADER},
                {"name": "Date", "value": "Mon, 20 Jan 2026 10:00:00 +0000"},
                {"name": "References", "value": "<earlier-msg@test.example.com>"},
            ],
            "body": {
                "size": 24,
                "data": base64.urlsafe_b64encode(b"Test message body content").decode(),
            },
        },
        "sizeEstimate": 1024,
        "historyId": "12345",
        "internalDate": "1737370800000",
    }


@pytest.fixture
def sample_message_html_response():
    """
    Sample Gmail API message response with HTML body.

    SECURITY: Uses only generic test data.
    """
    html_content = "<html><body><p>This is a <strong>test</strong> message.</p></body></html>"

    return {
        "id": "msg-test-002",
        "threadId": TEST_THREAD_ID,
        "labelIds": ["INBOX"],
        "payload": {
            "partId": "",
            "mimeType": "multipart/alternative",
            "headers": [
                {"name": "Subject", "value": "HTML Test Subject"},
                {"name": "From", "value": f"Test Sender <{TEST_SENDER_EMAIL}>"},
                {"name": "To", "value": TEST_RECIPIENT_EMAIL},
                {"name": "Message-ID", "value": "<test-msg-002@mail.test.example.com>"},
                {"name": "Date", "value": "Mon, 20 Jan 2026 11:00:00 +0000"},
            ],
            "parts": [
                {
                    "partId": "0",
                    "mimeType": "text/plain",
                    "body": {
                        "size": 20,
                        "data": base64.urlsafe_b64encode(b"This is a test message.").decode(),
                    },
                },
                {
                    "partId": "1",
                    "mimeType": "text/html",
                    "body": {
                        "size": len(html_content),
                        "data": base64.urlsafe_b64encode(html_content.encode()).decode(),
                    },
                },
            ],
        },
    }


@pytest.fixture
def sample_draft_response():
    """
    Sample Gmail API draft creation response.

    SECURITY: Uses only generic test data.
    """
    return {
        "id": TEST_DRAFT_ID,
        "message": {
            "id": "msg-from-draft-001",
            "threadId": TEST_THREAD_ID,
            "labelIds": ["DRAFT"],
        },
    }


@pytest.fixture
def sample_thread_response(sample_message_response):
    """
    Sample Gmail API thread response with multiple messages.

    SECURITY: Uses only generic test data.
    """
    reply_message = {
        "id": "msg-test-reply-001",
        "threadId": TEST_THREAD_ID,
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Re: Test Subject"},
                {"name": "From", "value": f"Test Recipient <{TEST_RECIPIENT_EMAIL}>"},
                {"name": "To", "value": TEST_SENDER_EMAIL},
                {"name": "Message-ID", "value": "<test-msg-reply-001@mail.test.example.com>"},
                {"name": "In-Reply-To", "value": TEST_MESSAGE_ID_HEADER},
                {"name": "References", "value": TEST_MESSAGE_ID_HEADER},
                {"name": "Date", "value": "Mon, 20 Jan 2026 12:00:00 +0000"},
            ],
            "body": {
                "data": base64.urlsafe_b64encode(b"This is a reply.").decode(),
            },
        },
    }

    return {
        "id": TEST_THREAD_ID,
        "historyId": "12346",
        "messages": [sample_message_response, reply_message],
    }


# =============================================================================
# Async helpers
# =============================================================================

@pytest.fixture
def async_mock():
    """Helper to create AsyncMock objects."""
    return AsyncMock


# =============================================================================
# Test markers
# =============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
