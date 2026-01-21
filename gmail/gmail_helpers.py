"""
Gmail helper functions for threading and formatting.

This module provides utility functions for:
- Extracting threading information from Gmail messages
- Building RFC 2822 compliant References headers
- Formatting subjects for replies and forwards
- Formatting quoted message bodies
- Converting plain text to HTML

SECURITY NOTE:
This file contains no credentials, personal data, or environment-specific
configuration. All such data must be passed as parameters at runtime.
"""

import re
from typing import Optional, Dict, Any
from email.utils import parseaddr


def extract_threading_info(message: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract threading information from a Gmail message.

    Parses the Gmail API message response to extract all information
    needed to create a properly threaded reply.

    Args:
        message: Gmail API message response (from messages.get)

    Returns:
        Dict with keys:
            - thread_id: Gmail thread ID
            - message_id: RFC 2822 Message-ID header value
            - subject: Email subject
            - from_email: Sender's email address
            - from_name: Sender's display name (may be empty)
            - references: Existing References header (may be empty)
            - date: Date header value
    """
    result = {
        "thread_id": message.get("threadId", ""),
        "message_id": "",
        "subject": "",
        "from_email": "",
        "from_name": "",
        "references": "",
        "date": "",
    }

    headers = message.get("payload", {}).get("headers", [])
    for header in headers:
        name = header.get("name", "").lower()
        value = header.get("value", "")

        if name == "message-id":
            result["message_id"] = value
        elif name == "subject":
            result["subject"] = value
        elif name == "from":
            # Parse "Display Name <email@example.com>" format
            parsed_name, parsed_email = parseaddr(value)
            result["from_name"] = parsed_name
            result["from_email"] = parsed_email
        elif name == "references":
            result["references"] = value
        elif name == "date":
            result["date"] = value

    return result


def extract_recipients(message: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract recipient information from a Gmail message.

    Args:
        message: Gmail API message response

    Returns:
        Dict with keys:
            - to: To header value
            - cc: Cc header value (may be empty)
    """
    result = {
        "to": "",
        "cc": "",
    }

    headers = message.get("payload", {}).get("headers", [])
    for header in headers:
        name = header.get("name", "").lower()
        value = header.get("value", "")

        if name == "to":
            result["to"] = value
        elif name == "cc":
            result["cc"] = value

    return result


def build_references_chain(
    existing_references: Optional[str],
    in_reply_to: str
) -> str:
    """
    Build RFC 2822 References header chain.

    The References header should contain all Message-IDs in the thread,
    with the most recent message's ID at the end.

    Args:
        existing_references: Current References header from the message
                            being replied to (may be None or empty)
        in_reply_to: Message-ID of the message being replied to

    Returns:
        Updated References chain suitable for the reply

    Example:
        >>> build_references_chain(None, "<msg1@example.com>")
        '<msg1@example.com>'
        >>> build_references_chain("<msg1@example.com>", "<msg2@example.com>")
        '<msg1@example.com> <msg2@example.com>'
    """
    if not in_reply_to:
        return existing_references or ""

    if existing_references:
        # Append new message-id to existing chain
        return f"{existing_references} {in_reply_to}"
    else:
        # Start new chain with the message being replied to
        return in_reply_to


def format_reply_subject(original_subject: str) -> str:
    """
    Format subject line for a reply email.

    Adds "Re: " prefix if not already present. Handles various
    case variations of existing "Re:" prefix.

    Args:
        original_subject: Original email subject

    Returns:
        Subject with "Re: " prefix

    Example:
        >>> format_reply_subject("Hello")
        'Re: Hello'
        >>> format_reply_subject("Re: Hello")
        'Re: Hello'
        >>> format_reply_subject("RE: Hello")
        'RE: Hello'
    """
    if not original_subject:
        return "Re:"

    # Check for existing Re: (case-insensitive, with optional whitespace)
    if re.match(r"^re:\s*", original_subject, re.IGNORECASE):
        return original_subject

    return f"Re: {original_subject}"


def format_forward_subject(original_subject: str) -> str:
    """
    Format subject line for a forwarded email.

    Adds "Fwd: " prefix if not already present. Handles various
    common forward prefix formats (Fwd:, FW:, Fw:).

    Args:
        original_subject: Original email subject

    Returns:
        Subject with "Fwd: " prefix

    Example:
        >>> format_forward_subject("Hello")
        'Fwd: Hello'
        >>> format_forward_subject("Fwd: Hello")
        'Fwd: Hello'
        >>> format_forward_subject("FW: Hello")
        'FW: Hello'
    """
    if not original_subject:
        return "Fwd:"

    # Check for existing Fwd:/FW:/Fw: (case-insensitive)
    if re.match(r"^(fwd?|fw):\s*", original_subject, re.IGNORECASE):
        return original_subject

    return f"Fwd: {original_subject}"


def format_quoted_body(
    original_body: str,
    from_name: str,
    from_email: str,
    date: str,
    as_html: bool = True
) -> str:
    """
    Format original message as a quoted reply.

    Creates a properly formatted quote block with attribution line
    showing who wrote the original message and when.

    Args:
        original_body: Original message body (plain text)
        from_name: Sender's display name
        from_email: Sender's email address
        date: Date of original message
        as_html: If True, return HTML format; if False, plain text

    Returns:
        Formatted quoted message

    SECURITY NOTE: Parameters must not contain sensitive data in tests.
    """
    sender = from_name if from_name else from_email

    if as_html:
        # Escape HTML entities in the original body
        escaped_body = (
            original_body
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        # Convert newlines to HTML breaks
        quoted_body = escaped_body.replace("\n", "<br>")

        return f"""<br><br>
<div style="border-left: 2px solid #ccc; padding-left: 10px; margin-left: 5px; color: #555;">
<p style="margin: 0 0 10px 0;">On {date}, {sender} &lt;{from_email}&gt; wrote:</p>
<div>{quoted_body}</div>
</div>"""
    else:
        # Plain text quote format with ">" prefix
        quoted_lines = [f"> {line}" for line in original_body.split("\n")]
        quoted_body = "\n".join(quoted_lines)
        return f"\n\nOn {date}, {sender} <{from_email}> wrote:\n{quoted_body}"


def format_forward_body(
    original_body: str,
    from_name: str,
    from_email: str,
    to: str,
    date: str,
    subject: str,
    comment: str = "",
    as_html: bool = True
) -> str:
    """
    Format a message for forwarding.

    Creates a properly formatted forward with header block showing
    original message metadata.

    Args:
        original_body: Original message body (plain text)
        from_name: Original sender's display name
        from_email: Original sender's email address
        to: Original recipient(s)
        date: Date of original message
        subject: Original subject
        comment: Optional comment to add before forwarded message
        as_html: If True, return HTML format; if False, plain text

    Returns:
        Formatted forward message

    SECURITY NOTE: Parameters must not contain sensitive data in tests.
    """
    sender = from_name if from_name else from_email

    if as_html:
        # Escape HTML entities in the original body
        escaped_body = (
            original_body
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        forwarded_body = escaped_body.replace("\n", "<br>")

        comment_html = convert_newlines_to_html(comment) if comment else ""

        return f"""{comment_html}<br><br>
---------- Forwarded message ----------<br>
<b>From:</b> {sender} &lt;{from_email}&gt;<br>
<b>Date:</b> {date}<br>
<b>Subject:</b> {subject}<br>
<b>To:</b> {to}<br>
<br>
{forwarded_body}"""
    else:
        header = f"""
---------- Forwarded message ----------
From: {sender} <{from_email}>
Date: {date}
Subject: {subject}
To: {to}

"""
        return f"{comment}\n{header}{original_body}" if comment else f"{header}{original_body}"


def convert_newlines_to_html(text: str) -> str:
    """
    Convert plain text newlines to HTML line breaks.

    Handles both paragraph breaks (double newlines) and
    single line breaks appropriately. Also handles escaped
    newlines (literal \\n strings) that may come from JSON
    transport or MCP tool calls.

    Args:
        text: Plain text with \\n newlines (real or escaped)

    Returns:
        Text with <br> tags instead of newlines

    Example:
        >>> convert_newlines_to_html("Hello\\n\\nWorld")
        'Hello<br><br>World'
        >>> convert_newlines_to_html("Line 1\\nLine 2")
        'Line 1<br>Line 2'
        >>> convert_newlines_to_html("Line 1\\\\nLine 2")  # escaped
        'Line 1<br>Line 2'
    """
    if not text:
        return ""

    # First handle escaped newlines (literal backslash-n from JSON/MCP transport)
    # Must do this BEFORE handling real newlines
    # Handle double escaped newlines first (paragraphs)
    text = text.replace("\\n\\n", "<br><br>")
    # Then single escaped newlines
    text = text.replace("\\n", "<br>")

    # Then handle real newlines (for direct function calls)
    # Double newlines (paragraphs)
    text = text.replace("\n\n", "<br><br>")
    # Single newlines
    text = text.replace("\n", "<br>")

    return text


def _extract_email_address(addr: str) -> str:
    """
    Extract the email address from a potentially formatted string.

    Handles formats like:
    - "user@example.com"
    - "Display Name <user@example.com>"
    - "<user@example.com>"

    Args:
        addr: Email string, possibly with display name

    Returns:
        Just the email address, lowercased
    """
    _, email = parseaddr(addr)
    return email.lower() if email else addr.lower()


def filter_reply_all_recipients(
    original_from: str,
    original_to: str,
    original_cc: str,
    user_email: str
) -> tuple[str, str]:
    """
    Filter recipients for reply-all, excluding the user's own email.

    Combines original sender, To, and Cc recipients, removing
    the user's own email address to avoid sending to self.

    Args:
        original_from: Original sender email
        original_to: Original To header value
        original_cc: Original Cc header value
        user_email: Current user's email (to exclude)

    Returns:
        Tuple of (to_addresses, cc_addresses)
    """
    user_email_lower = user_email.lower()

    def is_user_email(addr: str) -> bool:
        """Check if addr matches user's email (exact match, not substring)."""
        extracted = _extract_email_address(addr)
        return extracted == user_email_lower

    # Start with original sender as primary recipient
    to_addresses = []
    if original_from and not is_user_email(original_from):
        to_addresses.append(original_from)

    # Process original To recipients
    if original_to:
        for addr in original_to.split(","):
            addr = addr.strip()
            if addr and not is_user_email(addr):
                if addr not in to_addresses:
                    to_addresses.append(addr)

    # Process original Cc recipients
    cc_addresses = []
    if original_cc:
        for addr in original_cc.split(","):
            addr = addr.strip()
            if addr and not is_user_email(addr):
                if addr not in to_addresses and addr not in cc_addresses:
                    cc_addresses.append(addr)

    return ", ".join(to_addresses), ", ".join(cc_addresses)
