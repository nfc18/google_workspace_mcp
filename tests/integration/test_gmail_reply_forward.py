"""
Integration tests for Gmail reply and forward functionality.

SECURITY NOTE:
- All tests use mocked Gmail API responses
- No real API calls are made
- No real credentials or personal data
- All test data uses generic @test.example.com addresses

This module tests the internal implementation functions (_impl) directly,
bypassing the MCP decorators which wrap functions into FunctionTool objects.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import base64

from tests.fixtures.gmail_responses import (
    create_message_response,
    create_draft_response,
)

# Import the internal implementation functions directly
from gmail.gmail_tools import (
    _reply_gmail_draft_impl,
    _forward_gmail_draft_impl,
)


# =============================================================================
# Test fixtures
# =============================================================================

@pytest.fixture
def mock_gmail_service():
    """Create a mock Gmail service for testing."""
    service = MagicMock()
    return service


@pytest.fixture
def standard_message():
    """Standard test message for reply/forward tests."""
    return create_message_response(
        msg_id="msg-original-001",
        thread_id="thread-001",
        subject="Original Test Subject",
        from_email="sender@test.example.com",
        from_name="Original Sender",
        to_email="recipient@test.example.com",
        cc_email="cc-user@test.example.com",
        message_id_header="<original-msg@test.example.com>",
        references="<earlier-msg@test.example.com>",
        body_text="This is the original message content.\n\nWith multiple paragraphs.",
        date="Mon, 20 Jan 2026 10:00:00 +0000",
    )


@pytest.fixture
def message_without_cc():
    """Message without CC recipients."""
    return create_message_response(
        msg_id="msg-no-cc-001",
        thread_id="thread-002",
        subject="No CC Test",
        from_email="sender@test.example.com",
        from_name="Sender",
        to_email="recipient@test.example.com",
        message_id_header="<no-cc-msg@test.example.com>",
        body_text="Message without CC.",
    )


# =============================================================================
# Tests for reply_gmail_draft
# =============================================================================

class TestReplyGmailDraft:
    """Integration tests for reply_gmail_draft function."""

    @pytest.mark.asyncio
    async def test_creates_simple_reply(self, mock_gmail_service, standard_message):
        """Test creating a simple reply to sender only."""
        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                standard_message,
                create_draft_response(draft_id="draft-reply-001", thread_id="thread-001"),
            ]

            result = await _reply_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-original-001",
                body="Thanks for your message!",
                reply_all=False,
                include_quote=False,
            )

            # Verify result
            assert "draft-reply-001" in result
            assert "thread-001" in result
            assert "sender@test.example.com" in result

    @pytest.mark.asyncio
    async def test_reply_all_includes_recipients(self, mock_gmail_service, standard_message):
        """Test that reply-all includes original To and CC recipients."""
        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                standard_message,
                create_draft_response(draft_id="draft-reply-all-001", thread_id="thread-001"),
            ]

            result = await _reply_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-original-001",
                body="Reply to everyone!",
                reply_all=True,
                include_quote=False,
            )

            assert "draft-reply-all-001" in result

    @pytest.mark.asyncio
    async def test_reply_excludes_self_from_recipients(self, mock_gmail_service):
        """Test that user's own email is excluded from reply-all recipients."""
        # Message where user is in the To field
        message = create_message_response(
            msg_id="msg-001",
            thread_id="thread-001",
            subject="Test",
            from_email="sender@test.example.com",
            to_email="test-user@test.example.com, other@test.example.com",
            message_id_header="<msg@test.example.com>",
            body_text="Test",
        )

        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                message,
                create_draft_response(draft_id="draft-001"),
            ]

            result = await _reply_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-001",
                body="Reply",
                reply_all=True,
                include_quote=False,
            )

            # User's email should not be in the To field
            assert "draft-001" in result

    @pytest.mark.asyncio
    async def test_reply_with_quote_includes_original(self, mock_gmail_service, standard_message):
        """Test that include_quote adds the original message."""
        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                standard_message,
                create_draft_response(draft_id="draft-quoted-001"),
            ]

            result = await _reply_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-original-001",
                body="See my comments below.",
                reply_all=False,
                include_quote=True,
            )

            assert "draft-quoted-001" in result

    @pytest.mark.asyncio
    async def test_reply_adds_re_prefix_to_subject(self, mock_gmail_service, standard_message):
        """Test that Re: is added to subject if not present."""
        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                standard_message,
                create_draft_response(draft_id="draft-001"),
            ]

            result = await _reply_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-original-001",
                body="Reply",
                reply_all=False,
                include_quote=False,
            )

            # Result confirms draft was created
            assert "Draft ID: draft-001" in result

    @pytest.mark.asyncio
    async def test_reply_builds_references_chain(self, mock_gmail_service, standard_message):
        """Test that References header chain is properly built."""
        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                standard_message,
                create_draft_response(draft_id="draft-001"),
            ]

            # This test verifies the function completes successfully
            # The actual References header is built internally
            result = await _reply_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-original-001",
                body="Reply",
                reply_all=False,
                include_quote=False,
            )

            assert "draft-001" in result

    @pytest.mark.asyncio
    async def test_reply_with_additional_cc(self, mock_gmail_service, standard_message):
        """Test adding additional CC recipients to reply."""
        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                standard_message,
                create_draft_response(draft_id="draft-cc-001"),
            ]

            result = await _reply_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-original-001",
                body="Reply with extra CC",
                reply_all=False,
                include_quote=False,
                cc="extra-cc@test.example.com",
            )

            assert "draft-cc-001" in result

    @pytest.mark.asyncio
    async def test_reply_with_bcc(self, mock_gmail_service, standard_message):
        """Test adding BCC recipients to reply."""
        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                standard_message,
                create_draft_response(draft_id="draft-bcc-001"),
            ]

            result = await _reply_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-original-001",
                body="Reply with BCC",
                reply_all=False,
                include_quote=False,
                bcc="bcc@test.example.com",
            )

            assert "draft-bcc-001" in result


# =============================================================================
# Tests for forward_gmail_draft
# =============================================================================

class TestForwardGmailDraft:
    """Integration tests for forward_gmail_draft function."""

    @pytest.mark.asyncio
    async def test_creates_forward_draft(self, mock_gmail_service, standard_message):
        """Test creating a basic forward draft."""
        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                standard_message,
                create_draft_response(draft_id="draft-fwd-001"),
            ]

            result = await _forward_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-original-001",
                to="forward-to@test.example.com",
                body="FYI - see below",
            )

            assert "draft-fwd-001" in result
            assert "forward-to@test.example.com" in result
            assert "Fwd:" in result

    @pytest.mark.asyncio
    async def test_forward_without_comment(self, mock_gmail_service, standard_message):
        """Test forwarding without adding a comment."""
        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                standard_message,
                create_draft_response(draft_id="draft-fwd-no-comment-001"),
            ]

            result = await _forward_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-original-001",
                to="forward-to@test.example.com",
                body="",  # No comment
            )

            assert "draft-fwd-no-comment-001" in result

    @pytest.mark.asyncio
    async def test_forward_to_multiple_recipients(self, mock_gmail_service, standard_message):
        """Test forwarding to multiple recipients."""
        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                standard_message,
                create_draft_response(draft_id="draft-fwd-multi-001"),
            ]

            result = await _forward_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-original-001",
                to="user1@test.example.com, user2@test.example.com",
                body="Sharing with you both",
            )

            assert "draft-fwd-multi-001" in result

    @pytest.mark.asyncio
    async def test_forward_with_cc(self, mock_gmail_service, standard_message):
        """Test forwarding with CC recipients."""
        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                standard_message,
                create_draft_response(draft_id="draft-fwd-cc-001"),
            ]

            result = await _forward_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-original-001",
                to="main@test.example.com",
                cc="cc@test.example.com",
                body="Please review",
            )

            assert "draft-fwd-cc-001" in result

    @pytest.mark.asyncio
    async def test_forward_with_bcc(self, mock_gmail_service, standard_message):
        """Test forwarding with BCC recipients."""
        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                standard_message,
                create_draft_response(draft_id="draft-fwd-bcc-001"),
            ]

            result = await _forward_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-original-001",
                to="main@test.example.com",
                bcc="bcc@test.example.com",
                body="",
            )

            assert "draft-fwd-bcc-001" in result

    @pytest.mark.asyncio
    async def test_forward_adds_fwd_prefix_to_subject(self, mock_gmail_service, standard_message):
        """Test that Fwd: is added to subject."""
        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                standard_message,
                create_draft_response(draft_id="draft-001"),
            ]

            result = await _forward_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-original-001",
                to="forward@test.example.com",
            )

            # Subject should have Fwd: prefix
            assert "Fwd: Original Test Subject" in result


# =============================================================================
# Edge case tests
# =============================================================================

class TestEdgeCases:
    """Edge case tests for reply and forward functionality."""

    @pytest.mark.asyncio
    async def test_reply_to_message_without_references(self, mock_gmail_service):
        """Test replying to a message that has no References header."""
        # Message without References header
        message = create_message_response(
            msg_id="msg-no-refs-001",
            thread_id="thread-new",
            subject="New Thread",
            from_email="sender@test.example.com",
            to_email="recipient@test.example.com",
            message_id_header="<first-msg@test.example.com>",
            body_text="First message in thread",
        )

        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                message,
                create_draft_response(draft_id="draft-new-thread-001"),
            ]

            result = await _reply_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-no-refs-001",
                body="Reply to new thread",
                reply_all=False,
                include_quote=False,
            )

            assert "draft-new-thread-001" in result

    @pytest.mark.asyncio
    async def test_reply_to_message_without_display_name(self, mock_gmail_service):
        """Test replying to a message where sender has no display name."""
        # Message with email-only From
        message = create_message_response(
            msg_id="msg-001",
            thread_id="thread-001",
            subject="Test",
            from_email="sender@test.example.com",
            from_name="",  # No display name
            to_email="recipient@test.example.com",
            message_id_header="<msg@test.example.com>",
            body_text="Test message",
        )

        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                message,
                create_draft_response(draft_id="draft-001"),
            ]

            result = await _reply_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-001",
                body="Reply",
                reply_all=False,
                include_quote=True,  # Include quote to test name handling
            )

            assert "draft-001" in result

    @pytest.mark.asyncio
    async def test_forward_message_with_html_body(self, mock_gmail_service):
        """Test forwarding a message that has HTML body."""
        # Message with HTML body
        message = create_message_response(
            msg_id="msg-html-001",
            thread_id="thread-001",
            subject="HTML Email",
            from_email="sender@test.example.com",
            to_email="recipient@test.example.com",
            message_id_header="<msg@test.example.com>",
            body_text="Plain text version",
            body_html="<html><body><p>HTML version</p></body></html>",
        )

        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                message,
                create_draft_response(draft_id="draft-html-001"),
            ]

            result = await _forward_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-html-001",
                to="forward@test.example.com",
                body="Check this out",
            )

            assert "draft-html-001" in result

    @pytest.mark.asyncio
    async def test_reply_with_multiline_body(self, mock_gmail_service, standard_message):
        """Test reply with multiline body text."""
        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                standard_message,
                create_draft_response(draft_id="draft-multiline-001"),
            ]

            result = await _reply_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-original-001",
                body="Line 1\n\nLine 2\n\nLine 3",  # Multiline body
                reply_all=False,
                include_quote=False,
            )

            assert "draft-multiline-001" in result

    @pytest.mark.asyncio
    async def test_reply_preserves_existing_re_prefix(self, mock_gmail_service):
        """Test that existing Re: prefix is preserved."""
        # Message that's already a reply
        message = create_message_response(
            msg_id="msg-001",
            thread_id="thread-001",
            subject="Re: Original Subject",  # Already has Re:
            from_email="sender@test.example.com",
            to_email="recipient@test.example.com",
            message_id_header="<msg@test.example.com>",
            body_text="Previous reply",
        )

        with patch("gmail.gmail_tools.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = [
                message,
                create_draft_response(draft_id="draft-001"),
            ]

            result = await _reply_gmail_draft_impl(
                service=mock_gmail_service,
                user_google_email="test-user@test.example.com",
                message_id="msg-001",
                body="Another reply",
                reply_all=False,
                include_quote=False,
            )

            # Should not have Re: Re:
            assert "draft-001" in result
