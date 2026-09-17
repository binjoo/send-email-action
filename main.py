#!/usr/bin/env python3
"""Send an email via SMTP.

GitHub Action entry point, implemented with the Python standard library only.
The GitHub runner exposes every `with:` input of action.yml as an INPUT_<NAME>
environment variable (upper-cased), which is what this script reads.
"""

import glob
import mimetypes
import os
import re
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formataddr, make_msgid, parseaddr

SMTP_TIMEOUT = 60  # seconds

VALID_SECURE = {"auto", "ssl", "starttls", "none"}


def log(message):
    print(message, flush=True)


def fail(message):
    print(f"::error::{message}", flush=True)
    sys.exit(1)


def get_input(name, default="", *, required=False, strip=True):
    value = os.getenv("INPUT_" + name.upper().replace("-", "_"))
    if value is None:
        value = ""
    if strip:
        value = value.strip()
    if value == "":
        if required:
            fail(f"Missing required input '{name}'.")
        return default
    return value


def parse_addresses(raw, input_name):
    """Split an address list on comma / semicolon / newline.

    Returns (header_tokens, envelope_addresses); each token may optionally use
    the "Display Name <addr@example.com>" form.
    """
    tokens = [token.strip() for token in re.split(r"[,;\r\n]+", raw) if token.strip()]
    envelope = [parseaddr(token)[1] for token in tokens]
    invalid = not tokens or any(
        not addr or not re.fullmatch(r"[^@\s]+@[^@\s]+", addr) for addr in envelope
    )
    if invalid:
        fail(f"Input '{input_name}' contains an invalid email address: {raw!r}")
    return tokens, envelope


def normalize_content_type(raw):
    value = raw.strip().lower()
    aliases = {"plain": "text/plain", "text": "text/plain", "html": "text/html"}
    value = aliases.get(value, value)
    if value not in ("text/plain", "text/html"):
        fail(f"Unsupported content_type '{raw}'. Use 'text/plain' or 'text/html'.")
    return value


def parse_attachments(raw):
    """Return a list of (path, filename) pairs from a newline/comma/semicolon
    separated list of file paths or glob patterns (e.g. "dist/*.zip")."""
    pairs = []
    for pattern in (part.strip() for part in re.split(r"[,;\r\n]+", raw)):
        if not pattern:
            continue
        matched = [path for path in sorted(glob.glob(pattern, recursive=True)) if os.path.isfile(path)]
        if matched:
            pairs.extend((path, os.path.basename(path)) for path in matched)
        elif os.path.isfile(pattern):
            pairs.append((pattern, os.path.basename(pattern)))
        else:
            fail(f"Input 'attachments': no file matches '{pattern}'.")
    return pairs


def build_message(*, subject, body, content_type, from_addr, sender, to_tokens, cc_tokens):
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((sender, from_addr)) if sender else from_addr
    message["To"] = ", ".join(to_tokens)
    if cc_tokens:
        message["Cc"] = ", ".join(cc_tokens)
    domain = from_addr.rsplit("@", 1)[-1] or "localhost"
    message["Message-ID"] = make_msgid(domain=domain)

    if content_type == "text/html":
        message.set_content(body, subtype="html")
    else:
        message.set_content(body)
    return message


def add_attachments(message, attachments):
    for path, filename in attachments:
        mime_type, encoding = mimetypes.guess_type(path)
        if mime_type is None or encoding is not None:
            mime_type = "application/octet-stream"
        maintype, _, subtype = mime_type.partition("/")
        with open(path, "rb") as handle:
            message.add_attachment(handle.read(), maintype=maintype, subtype=subtype, filename=filename)


def connect(host, port, secure):
    context = ssl.create_default_context()
    if secure == "ssl":
        return smtplib.SMTP_SSL(host, port, context=context, timeout=SMTP_TIMEOUT)
    server = smtplib.SMTP(host, port, timeout=SMTP_TIMEOUT)
    server.ehlo()
    if secure == "starttls":
        server.starttls(context=context)
        server.ehlo()
    return server


def set_output(name, value):
    output_path = os.getenv("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def main():
    host = get_input("smtp_host", required=True)
    port_raw = get_input("smtp_port", "465")
    try:
        port = int(port_raw)
    except ValueError:
        fail(f"Input 'smtp_port' must be an integer, got '{port_raw}'.")
    if not 1 <= port <= 65535:
        fail(f"Input 'smtp_port' is out of range: {port}.")

    username = get_input("smtp_username", required=True)
    password = get_input("smtp_password", required=True, strip=False)

    to_tokens, to_envelope = parse_addresses(get_input("to_mail", required=True), "to_mail")
    cc_raw = get_input("cc")
    bcc_raw = get_input("bcc")
    cc_tokens, cc_envelope = parse_addresses(cc_raw, "cc") if cc_raw else ([], [])
    bcc_tokens, bcc_envelope = parse_addresses(bcc_raw, "bcc") if bcc_raw else ([], [])

    # Do not blindly assume the SMTP username is an email address; fall back to
    # it only when it looks like one, otherwise an explicit 'from' is required.
    from_addr = get_input("from")
    if not from_addr and re.fullmatch(r"[^@\s]+@[^@\s]+", username):
        from_addr = username
    if not from_addr:
        fail("Input 'from' is required when 'smtp_username' is not an email address.")
    sender = get_input("sender")
    subject = get_input("subject", required=True)
    body = get_input("body", required=True)
    content_type = normalize_content_type(get_input("content_type", "text/plain"))

    attachments = parse_attachments(get_input("attachments"))
    for path, _ in attachments:
        if not os.path.isfile(path):
            fail(f"Input 'attachments': file not found: '{path}'.")

    secure = get_input("secure", "auto").lower()
    if secure not in VALID_SECURE:
        fail(f"Input 'secure' must be one of {sorted(VALID_SECURE)}, got '{secure}'.")
    if secure == "auto":
        secure = "ssl" if port == 465 else "starttls"

    message = build_message(
        subject=subject,
        body=body,
        content_type=content_type,
        from_addr=from_addr,
        sender=sender,
        to_tokens=to_tokens,
        cc_tokens=cc_tokens,
    )
    add_attachments(message, attachments)

    log(f"SMTP server : {host}:{port} (TLS mode: {secure})")
    log(f"From        : {from_addr}" + (f" <{sender}>" if sender else ""))
    log(f"To          : {', '.join(to_tokens)}")
    if cc_tokens:
        log(f"Cc          : {', '.join(cc_tokens)}")
    log(f"Subject     : {subject}")
    log(f"Attachments : {len(attachments)} file(s)")

    recipients = to_envelope + cc_envelope + bcc_envelope
    try:
        server = connect(host, port, secure)
    except (smtplib.SMTPException, OSError) as exc:
        fail(f"Cannot connect to {host}:{port}: {exc}.")

    try:
        server.login(username, password)
        refused = server.send_message(message, from_addr=from_addr, to_addrs=recipients)
        if refused:
            fail(f"SMTP server refused some recipients: {refused}")
    except smtplib.SMTPAuthenticationError as exc:
        fail(f"SMTP authentication failed for '{username}': {exc}. "
             "Note: Gmail / QQ Mail / 163 Mail require an app-specific password here.")
    except (smtplib.SMTPException, OSError) as exc:
        fail(f"Failed to send email: {exc}.")
    finally:
        try:
            server.quit()
        except Exception:
            pass

    set_output("message_id", message["Message-ID"])
    log(f"Email sent successfully. Message-ID: {message['Message-ID']}")


if __name__ == "__main__":
    main()
