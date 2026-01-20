"""
Unit tests for Gmail helper functions.

SECURITY NOTE:
- All test data uses generic @test.example.com addresses
- No real personal data or credentials
- Tests are fully isolated and make no API calls
"""

import pytest
from gmail.gmail_helpers import (
    extract_threading_info,
    extract_recipients,
    build_references_chain,
    format_reply_subject,
    format_forward_subject,
    format_quoted_body,
    format_forward_body,
    convert_newlines_to_html,
    filter_reply_all_recipients,
    _extract_email_address,
)


class TestExtractThreadingInfo:
    """Tests for extract_threading_info function."""

    def test_extracts_all_fields(self, sample_message_response):
        """Test extraction of all threading fields from a complete message."""
        result = extract_threading_info(sample_message_response)

        assert result["thread_id"] == "thread-test-abc123"
        assert result["message_id"] == "<test-msg-001@mail.test.example.com>"
        assert result["subject"] == "Test Subject"
        assert result["from_email"] == "sender@test.example.com"
        assert result["from_name"] == "Test Sender"
        assert result["references"] == "<earlier-msg@test.example.com>"

    def test_handles_missing_headers(self):
        """Test handling of message with no headers."""
        message = {"threadId": "t123", "payload": {"headers": []}}
        result = extract_threading_info(message)

        assert result["thread_id"] == "t123"
        assert result["message_id"] == ""
        assert result["subject"] == ""
        assert result["from_email"] == ""
        assert result["from_name"] == ""

    def test_handles_missing_payload(self):
        """Test handling of message with no payload."""
        message = {"threadId": "t456"}
        result = extract_threading_info(message)

        assert result["thread_id"] == "t456"
        assert result["message_id"] == ""

    def test_parses_from_with_name(self):
        """Test parsing From header with display name."""
        message = {
            "threadId": "t1",
            "payload": {
                "headers": [
                    {"name": "From", "value": "John Doe <john@test.example.com>"}
                ]
            }
        }
        result = extract_threading_info(message)

        assert result["from_name"] == "John Doe"
        assert result["from_email"] == "john@test.example.com"

    def test_parses_from_email_only(self):
        """Test parsing From header with email only (no display name)."""
        message = {
            "threadId": "t1",
            "payload": {
                "headers": [
                    {"name": "From", "value": "john@test.example.com"}
                ]
            }
        }
        result = extract_threading_info(message)

        assert result["from_name"] == ""
        assert result["from_email"] == "john@test.example.com"

    def test_handles_quoted_display_name(self):
        """Test parsing From header with quoted display name."""
        message = {
            "threadId": "t1",
            "payload": {
                "headers": [
                    {"name": "From", "value": '"Doe, John" <john@test.example.com>'}
                ]
            }
        }
        result = extract_threading_info(message)

        assert result["from_name"] == "Doe, John"
        assert result["from_email"] == "john@test.example.com"


class TestExtractRecipients:
    """Tests for extract_recipients function."""

    def test_extracts_to_and_cc(self, sample_message_response):
        """Test extraction of To and Cc headers."""
        result = extract_recipients(sample_message_response)

        assert result["to"] == "recipient@test.example.com"
        assert result["cc"] == "cc-user@test.example.com"

    def test_handles_missing_cc(self):
        """Test handling when Cc header is missing."""
        message = {
            "payload": {
                "headers": [
                    {"name": "To", "value": "recipient@test.example.com"}
                ]
            }
        }
        result = extract_recipients(message)

        assert result["to"] == "recipient@test.example.com"
        assert result["cc"] == ""


class TestBuildReferencesChain:
    """Tests for build_references_chain function."""

    def test_starts_new_chain(self):
        """Test starting a new References chain."""
        result = build_references_chain(None, "<msg1@test.example.com>")
        assert result == "<msg1@test.example.com>"

    def test_starts_chain_from_empty_string(self):
        """Test starting chain when existing is empty string."""
        result = build_references_chain("", "<msg1@test.example.com>")
        assert result == "<msg1@test.example.com>"

    def test_appends_to_existing_chain(self):
        """Test appending to existing References chain."""
        result = build_references_chain(
            "<msg1@test.example.com>",
            "<msg2@test.example.com>"
        )
        assert result == "<msg1@test.example.com> <msg2@test.example.com>"

    def test_appends_to_long_chain(self):
        """Test appending to a longer existing chain."""
        existing = "<msg1@test.example.com> <msg2@test.example.com>"
        result = build_references_chain(existing, "<msg3@test.example.com>")
        assert result == "<msg1@test.example.com> <msg2@test.example.com> <msg3@test.example.com>"

    def test_handles_empty_in_reply_to(self):
        """Test handling when in_reply_to is empty."""
        result = build_references_chain("<existing@test.example.com>", "")
        assert result == "<existing@test.example.com>"

    def test_handles_both_empty(self):
        """Test handling when both parameters are empty."""
        result = build_references_chain("", "")
        assert result == ""

    def test_handles_none_and_empty(self):
        """Test handling when existing is None and in_reply_to is empty."""
        result = build_references_chain(None, "")
        assert result == ""


class TestFormatReplySubject:
    """Tests for format_reply_subject function."""

    def test_adds_re_prefix(self):
        """Test adding Re: prefix to subject without it."""
        assert format_reply_subject("Test Subject") == "Re: Test Subject"

    def test_preserves_existing_re(self):
        """Test that existing Re: prefix is preserved."""
        assert format_reply_subject("Re: Test Subject") == "Re: Test Subject"

    def test_preserves_uppercase_re(self):
        """Test that existing uppercase RE: is preserved."""
        assert format_reply_subject("RE: Test Subject") == "RE: Test Subject"

    def test_preserves_lowercase_re(self):
        """Test that existing lowercase re: is preserved."""
        assert format_reply_subject("re: Test Subject") == "re: Test Subject"

    def test_preserves_mixed_case_re(self):
        """Test that existing mixed case Re: is preserved."""
        assert format_reply_subject("Re: Test Subject") == "Re: Test Subject"

    def test_handles_empty_subject(self):
        """Test handling of empty subject."""
        assert format_reply_subject("") == "Re:"

    def test_handles_whitespace_after_re(self):
        """Test that Re: with extra whitespace is preserved."""
        assert format_reply_subject("Re:  Test Subject") == "Re:  Test Subject"


class TestFormatForwardSubject:
    """Tests for format_forward_subject function."""

    def test_adds_fwd_prefix(self):
        """Test adding Fwd: prefix to subject without it."""
        assert format_forward_subject("Test Subject") == "Fwd: Test Subject"

    def test_preserves_existing_fwd(self):
        """Test that existing Fwd: prefix is preserved."""
        assert format_forward_subject("Fwd: Test Subject") == "Fwd: Test Subject"

    def test_preserves_uppercase_fw(self):
        """Test that existing uppercase FW: is preserved."""
        assert format_forward_subject("FW: Test Subject") == "FW: Test Subject"

    def test_preserves_lowercase_fwd(self):
        """Test that existing lowercase fwd: is preserved."""
        assert format_forward_subject("fwd: Test Subject") == "fwd: Test Subject"

    def test_handles_fw_without_d(self):
        """Test that Fw: (without d) is recognized."""
        assert format_forward_subject("Fw: Test Subject") == "Fw: Test Subject"

    def test_handles_empty_subject(self):
        """Test handling of empty subject."""
        assert format_forward_subject("") == "Fwd:"


class TestFormatQuotedBody:
    """Tests for format_quoted_body function."""

    def test_html_format_basic(self):
        """Test basic HTML quote formatting."""
        result = format_quoted_body(
            original_body="Hello World",
            from_name="Test Sender",
            from_email="sender@test.example.com",
            date="Mon, 20 Jan 2026 10:00:00 +0000",
            as_html=True
        )

        assert "On Mon, 20 Jan 2026 10:00:00 +0000" in result
        assert "Test Sender" in result
        assert "sender@test.example.com" in result
        assert "Hello World" in result
        assert "border-left" in result  # HTML styling

    def test_html_escapes_special_chars(self):
        """Test that HTML special characters are escaped."""
        result = format_quoted_body(
            original_body="Test <script>alert('xss')</script>",
            from_name="Sender",
            from_email="sender@test.example.com",
            date="Mon, 20 Jan 2026",
            as_html=True
        )

        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_plain_text_format(self):
        """Test plain text quote formatting."""
        result = format_quoted_body(
            original_body="Hello\nWorld",
            from_name="Test Sender",
            from_email="sender@test.example.com",
            date="Mon, 20 Jan 2026",
            as_html=False
        )

        assert "> Hello" in result
        assert "> World" in result
        assert "Test Sender <sender@test.example.com> wrote:" in result

    def test_uses_email_when_no_name(self):
        """Test that email is used when display name is empty."""
        result = format_quoted_body(
            original_body="Hello",
            from_name="",
            from_email="sender@test.example.com",
            date="Mon, 20 Jan 2026",
            as_html=True
        )

        # Should show email address as sender
        assert "sender@test.example.com" in result


class TestFormatForwardBody:
    """Tests for format_forward_body function."""

    def test_html_format_with_comment(self):
        """Test HTML forward formatting with comment."""
        result = format_forward_body(
            original_body="Original content",
            from_name="Original Sender",
            from_email="original@test.example.com",
            to="recipient@test.example.com",
            date="Mon, 20 Jan 2026",
            subject="Original Subject",
            comment="FYI - see below",
            as_html=True
        )

        assert "FYI - see below" in result
        assert "Forwarded message" in result
        assert "Original Sender" in result
        assert "original@test.example.com" in result
        assert "Original Subject" in result
        assert "Original content" in result

    def test_html_format_without_comment(self):
        """Test HTML forward formatting without comment."""
        result = format_forward_body(
            original_body="Content",
            from_name="Sender",
            from_email="sender@test.example.com",
            to="recipient@test.example.com",
            date="Mon, 20 Jan 2026",
            subject="Subject",
            comment="",
            as_html=True
        )

        assert "Forwarded message" in result
        assert "Content" in result

    def test_plain_text_format(self):
        """Test plain text forward formatting."""
        result = format_forward_body(
            original_body="Content",
            from_name="Sender",
            from_email="sender@test.example.com",
            to="recipient@test.example.com",
            date="Mon, 20 Jan 2026",
            subject="Subject",
            comment="",
            as_html=False
        )

        assert "---------- Forwarded message ----------" in result
        assert "From: Sender <sender@test.example.com>" in result


class TestConvertNewlinesToHtml:
    """Tests for convert_newlines_to_html function."""

    def test_converts_double_newlines(self):
        """Test conversion of paragraph breaks."""
        result = convert_newlines_to_html("Para 1\n\nPara 2")
        assert result == "Para 1<br><br>Para 2"

    def test_converts_single_newlines(self):
        """Test conversion of single line breaks."""
        result = convert_newlines_to_html("Line 1\nLine 2")
        assert result == "Line 1<br>Line 2"

    def test_mixed_newlines(self):
        """Test conversion of mixed newlines."""
        result = convert_newlines_to_html("Para 1\n\nLine 1\nLine 2")
        assert result == "Para 1<br><br>Line 1<br>Line 2"

    def test_handles_empty_string(self):
        """Test handling of empty string."""
        result = convert_newlines_to_html("")
        assert result == ""

    def test_handles_no_newlines(self):
        """Test handling of text without newlines."""
        result = convert_newlines_to_html("No breaks here")
        assert result == "No breaks here"


class TestFilterReplyAllRecipients:
    """Tests for filter_reply_all_recipients function."""

    def test_excludes_user_email(self):
        """Test that user's own email is excluded."""
        to, cc = filter_reply_all_recipients(
            original_from="sender@test.example.com",
            original_to="me@test.example.com, other@test.example.com",
            original_cc="",
            user_email="me@test.example.com"
        )

        assert "me@test.example.com" not in to
        assert "sender@test.example.com" in to
        assert "other@test.example.com" in to

    def test_combines_to_and_cc(self):
        """Test that To and Cc are properly combined."""
        to, cc = filter_reply_all_recipients(
            original_from="sender@test.example.com",
            original_to="to1@test.example.com",
            original_cc="cc1@test.example.com, cc2@test.example.com",
            user_email="me@test.example.com"
        )

        assert "sender@test.example.com" in to
        assert "to1@test.example.com" in to
        assert "cc1@test.example.com" in cc
        assert "cc2@test.example.com" in cc

    def test_handles_empty_cc(self):
        """Test handling when Cc is empty."""
        to, cc = filter_reply_all_recipients(
            original_from="sender@test.example.com",
            original_to="to@test.example.com",
            original_cc="",
            user_email="me@test.example.com"
        )

        assert "sender@test.example.com" in to
        assert cc == ""

    def test_case_insensitive_email_match(self):
        """Test that email matching is case-insensitive."""
        to, cc = filter_reply_all_recipients(
            original_from="sender@test.example.com",
            original_to="ME@TEST.EXAMPLE.COM, other@test.example.com",
            original_cc="",
            user_email="me@test.example.com"
        )

        assert "ME@TEST.EXAMPLE.COM" not in to
        assert "other@test.example.com" in to

    def test_no_duplicates(self):
        """Test that duplicate addresses are removed."""
        to, cc = filter_reply_all_recipients(
            original_from="sender@test.example.com",
            original_to="sender@test.example.com, other@test.example.com",
            original_cc="sender@test.example.com",
            user_email="me@test.example.com"
        )

        # sender should only appear once
        assert to.count("sender@test.example.com") == 1

    def test_similar_email_not_filtered_substring_bug(self):
        """Test that similar emails are NOT incorrectly filtered (substring bug fix).

        BUG: Previously used substring matching which would incorrectly filter
        "mytest@test.example.com" when user_email was "test@test.example.com"
        because "test@test.example.com" is a substring of "mytest@test.example.com".
        """
        to, cc = filter_reply_all_recipients(
            original_from="sender@test.example.com",
            original_to="mytest@test.example.com, test@test.example.com",
            original_cc="",
            user_email="test@test.example.com"
        )

        # Parse the result into a list for precise checking
        to_list = [addr.strip() for addr in to.split(",")]

        # mytest@... should NOT be filtered (it's a different email!)
        assert "mytest@test.example.com" in to_list
        # test@... should be filtered (it's the user's email) - check exact match in list
        assert "test@test.example.com" not in to_list

    def test_email_with_display_name_filtered_correctly(self):
        """Test that emails with display names are extracted and filtered correctly."""
        to, cc = filter_reply_all_recipients(
            original_from="sender@test.example.com",
            original_to="Test User <test@test.example.com>, Other <other@test.example.com>",
            original_cc="",
            user_email="test@test.example.com"
        )

        # User's email with display name should be filtered
        assert "test@test.example.com" not in to
        assert "Test User <test@test.example.com>" not in to
        # Other should remain
        assert "other@test.example.com" in to or "Other <other@test.example.com>" in to


class TestExtractEmailAddress:
    """Tests for _extract_email_address helper function."""

    def test_plain_email(self):
        """Test extracting plain email address."""
        result = _extract_email_address("user@test.example.com")
        assert result == "user@test.example.com"

    def test_email_with_display_name(self):
        """Test extracting email from 'Display Name <email>' format."""
        result = _extract_email_address("John Doe <john@test.example.com>")
        assert result == "john@test.example.com"

    def test_email_in_angle_brackets_only(self):
        """Test extracting email from '<email>' format (no display name)."""
        result = _extract_email_address("<john@test.example.com>")
        assert result == "john@test.example.com"

    def test_quoted_display_name(self):
        """Test extracting email with quoted display name."""
        result = _extract_email_address('"Doe, John" <john@test.example.com>')
        assert result == "john@test.example.com"

    def test_returns_lowercase(self):
        """Test that result is always lowercase."""
        result = _extract_email_address("John Doe <JOHN@TEST.EXAMPLE.COM>")
        assert result == "john@test.example.com"

    def test_uppercase_plain_email(self):
        """Test that plain uppercase email is lowercased."""
        result = _extract_email_address("USER@TEST.EXAMPLE.COM")
        assert result == "user@test.example.com"

    def test_empty_string(self):
        """Test handling empty string."""
        result = _extract_email_address("")
        assert result == ""

    def test_malformed_fallback(self):
        """Test that malformed input falls back to lowercase of input."""
        result = _extract_email_address("not-an-email")
        assert result == "not-an-email"
