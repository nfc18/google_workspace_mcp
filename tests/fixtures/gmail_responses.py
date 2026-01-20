"""
Mock Gmail API responses for testing.

SECURITY NOTE:
- All data uses generic @test.example.com addresses
- No real credentials, API keys, or personal data
- No real Gmail message IDs or thread IDs
- These fixtures simulate Gmail API responses for testing only
"""

import base64
from typing import Dict, Any, List


def create_message_response(
    msg_id: str = "msg-test-001",
    thread_id: str = "thread-test-001",
    subject: str = "Test Subject",
    from_email: str = "sender@test.example.com",
    from_name: str = "Test Sender",
    to_email: str = "recipient@test.example.com",
    cc_email: str = None,
    message_id_header: str = "<test-msg-001@mail.test.example.com>",
    references: str = None,
    in_reply_to: str = None,
    body_text: str = "Test message body content",
    body_html: str = None,
    date: str = "Mon, 20 Jan 2026 10:00:00 +0000",
) -> Dict[str, Any]:
    """
    Create a mock Gmail message response.

    Args:
        msg_id: Gmail message ID
        thread_id: Gmail thread ID
        subject: Email subject
        from_email: Sender email address
        from_name: Sender display name
        to_email: Recipient email address
        cc_email: CC email address (optional)
        message_id_header: RFC 2822 Message-ID header
        references: References header (optional)
        in_reply_to: In-Reply-To header (optional)
        body_text: Plain text body content
        body_html: HTML body content (optional)
        date: Date header value

    Returns:
        Dict simulating Gmail API message response
    """
    headers = [
        {"name": "Subject", "value": subject},
        {"name": "From", "value": f"{from_name} <{from_email}>"},
        {"name": "To", "value": to_email},
        {"name": "Message-ID", "value": message_id_header},
        {"name": "Date", "value": date},
    ]

    if cc_email:
        headers.append({"name": "Cc", "value": cc_email})

    if references:
        headers.append({"name": "References", "value": references})

    if in_reply_to:
        headers.append({"name": "In-Reply-To", "value": in_reply_to})

    # Build payload based on whether we have HTML
    if body_html:
        payload = {
            "mimeType": "multipart/alternative",
            "headers": headers,
            "parts": [
                {
                    "partId": "0",
                    "mimeType": "text/plain",
                    "body": {
                        "size": len(body_text),
                        "data": base64.urlsafe_b64encode(body_text.encode()).decode(),
                    },
                },
                {
                    "partId": "1",
                    "mimeType": "text/html",
                    "body": {
                        "size": len(body_html),
                        "data": base64.urlsafe_b64encode(body_html.encode()).decode(),
                    },
                },
            ],
        }
    else:
        payload = {
            "mimeType": "text/plain",
            "headers": headers,
            "body": {
                "size": len(body_text),
                "data": base64.urlsafe_b64encode(body_text.encode()).decode(),
            },
        }

    return {
        "id": msg_id,
        "threadId": thread_id,
        "labelIds": ["INBOX"],
        "snippet": body_text[:50] + "..." if len(body_text) > 50 else body_text,
        "payload": payload,
        "sizeEstimate": 1024,
        "historyId": "12345",
        "internalDate": "1737370800000",
    }


def create_draft_response(
    draft_id: str = "draft-test-001",
    message_id: str = "msg-draft-001",
    thread_id: str = None,
) -> Dict[str, Any]:
    """
    Create a mock Gmail draft creation response.

    Args:
        draft_id: Draft ID
        message_id: Associated message ID
        thread_id: Thread ID (if reply/in a thread)

    Returns:
        Dict simulating Gmail API draft creation response
    """
    response = {
        "id": draft_id,
        "message": {
            "id": message_id,
            "labelIds": ["DRAFT"],
        },
    }

    if thread_id:
        response["message"]["threadId"] = thread_id

    return response


def create_thread_response(
    thread_id: str = "thread-test-001",
    messages: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a mock Gmail thread response.

    Args:
        thread_id: Thread ID
        messages: List of message responses (uses default if None)

    Returns:
        Dict simulating Gmail API thread response
    """
    if messages is None:
        # Create a simple two-message thread
        original = create_message_response(
            msg_id="msg-test-001",
            thread_id=thread_id,
            subject="Test Thread Subject",
            from_email="sender@test.example.com",
            from_name="Original Sender",
            to_email="recipient@test.example.com",
            message_id_header="<original@test.example.com>",
            body_text="This is the original message.",
        )

        reply = create_message_response(
            msg_id="msg-test-002",
            thread_id=thread_id,
            subject="Re: Test Thread Subject",
            from_email="recipient@test.example.com",
            from_name="Replier",
            to_email="sender@test.example.com",
            message_id_header="<reply@test.example.com>",
            in_reply_to="<original@test.example.com>",
            references="<original@test.example.com>",
            body_text="This is a reply.",
            date="Mon, 20 Jan 2026 11:00:00 +0000",
        )

        messages = [original, reply]

    return {
        "id": thread_id,
        "historyId": "12345",
        "messages": messages,
    }


# =============================================================================
# Edge case fixtures
# =============================================================================

def create_message_no_subject() -> Dict[str, Any]:
    """Message with no subject header."""
    return create_message_response(
        msg_id="msg-no-subject",
        subject="",
    )


def create_message_no_from_name() -> Dict[str, Any]:
    """Message with email only in From (no display name)."""
    response = create_message_response(msg_id="msg-no-name")
    # Override From header to be email-only
    for header in response["payload"]["headers"]:
        if header["name"] == "From":
            header["value"] = "sender@test.example.com"
            break
    return response


def create_message_long_references() -> Dict[str, Any]:
    """Message with long References chain (deep thread)."""
    refs = " ".join([
        f"<msg-{i}@test.example.com>" for i in range(10)
    ])
    return create_message_response(
        msg_id="msg-deep-thread",
        references=refs,
        in_reply_to="<msg-9@test.example.com>",
    )


def create_message_with_attachments() -> Dict[str, Any]:
    """Message with attachment metadata."""
    response = create_message_response(msg_id="msg-with-attachment")

    # Add attachment part
    response["payload"]["mimeType"] = "multipart/mixed"
    response["payload"]["parts"] = [
        {
            "partId": "0",
            "mimeType": "text/plain",
            "body": {
                "size": 24,
                "data": base64.urlsafe_b64encode(b"Message with attachment").decode(),
            },
        },
        {
            "partId": "1",
            "mimeType": "application/pdf",
            "filename": "test-document.pdf",
            "body": {
                "attachmentId": "attachment-id-001",
                "size": 12345,
            },
        },
    ]

    return response
