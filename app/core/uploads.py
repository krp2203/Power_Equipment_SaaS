import ipaddress
import os
import socket
import uuid
from contextlib import contextmanager
from io import BytesIO
from urllib.parse import urlparse

import requests
from flask import current_app
from PIL import Image
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8MB
MAX_SPREADSHEET_BYTES = 5 * 1024 * 1024  # 5MB
_EXT_BY_FORMAT = {'JPEG': '.jpg', 'PNG': '.png', 'GIF': '.gif', 'WEBP': '.webp'}


class UploadError(ValueError):
    """Raised when an uploaded file/URL fails validation. The message is safe
    to show directly to the user (flash message / JSON error)."""


def _validate_and_save_bytes(data, resource, org_id):
    """Shared core for both upload paths: never trusts a claimed extension or
    Content-Type - decodes the bytes with Pillow and saves under the format
    it actually detects, so the file on disk always matches its real content."""
    if not data:
        raise UploadError("The file is empty.")
    if len(data) > MAX_IMAGE_BYTES:
        raise UploadError(
            f"File is too large ({len(data) // (1024 * 1024)}MB). "
            f"Max size is {MAX_IMAGE_BYTES // (1024 * 1024)}MB."
        )
    try:
        img = Image.open(BytesIO(data))
        img.verify()
        fmt = (img.format or '').upper()
    except Exception:
        raise UploadError("That file doesn't look like a valid image.")

    ext = _EXT_BY_FORMAT.get(fmt)
    if not ext:
        raise UploadError(f"Unsupported image format '{fmt or 'unknown'}'.")

    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', resource, str(org_id))
    os.makedirs(upload_dir, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(upload_dir, unique_filename), 'wb') as fh:
        fh.write(data)
    return f"/static/uploads/{resource}/{org_id}/{unique_filename}"


def save_image_upload(file_storage, resource, org_id):
    """
    Validates and saves a browser-uploaded image to
    static/uploads/<resource>/<org_id>/, returning its public URL.
    Raises UploadError (with a user-facing message) on failure.
    """
    filename = secure_filename(file_storage.filename or '')
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise UploadError(
            f"Unsupported file type '{ext or '(none)'}'. "
            f"Allowed types: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}."
        )

    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size == 0:
        raise UploadError("The uploaded file is empty.")
    if size > MAX_IMAGE_BYTES:
        raise UploadError(
            f"File is too large ({size // (1024 * 1024)}MB). "
            f"Max size is {MAX_IMAGE_BYTES // (1024 * 1024)}MB."
        )

    data = file_storage.stream.read()
    file_storage.stream.seek(0)
    return _validate_and_save_bytes(data, resource, org_id)


def _is_safe_ip(ip):
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast)


def _resolve_safe_ip(hostname):
    """
    Resolves hostname and returns one IP to connect to, only if every address
    it resolves to is public - rejects loopback/private/link-local/reserved
    ranges, which specifically includes 169.254.169.254 (the cloud metadata
    endpoint, the classic SSRF target) along with the usual 10.x/172.16.x/
    192.168.x ranges and localhost. Returns None if unresolvable or unsafe.
    """
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return None
    if not infos:
        return None
    ips = []
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            return None
        if not _is_safe_ip(ip):
            return None
        ips.append(str(ip))
    return ips[0]


@contextmanager
def _pinned_dns(hostname, ip):
    """
    Forces socket.getaddrinfo to resolve `hostname` to the single IP already
    validated by _resolve_safe_ip, for the duration of the actual request.

    Closes the TOCTOU gap a plain "check the hostname, then let requests
    resolve it again" approach leaves open: DNS rebinding, where an
    attacker's DNS record legitimately resolves to a public IP at check time
    and is swapped to an internal one (e.g. 169.254.169.254) by the time the
    real connection happens moments later. Pinning the exact validated IP
    means there's no second, independent lookup to rebind.

    Only intercepts this one hostname - every other lookup (including ones
    from concurrent gevent greenlets, since this app runs under gunicorn's
    gevent worker) passes through unpatched. Narrow accepted trade-off: two
    concurrent imports fetching the same hostname at the same instant could
    share this pinned IP rather than each re-resolving independently: harmless
    for a low-traffic, operator-only bulk-import tool.
    """
    real_getaddrinfo = socket.getaddrinfo

    def pinned(host, *args, **kwargs):
        if host == hostname:
            return real_getaddrinfo(ip, *args, **kwargs)
        return real_getaddrinfo(host, *args, **kwargs)

    socket.getaddrinfo = pinned
    try:
        yield
    finally:
        socket.getaddrinfo = real_getaddrinfo


def save_image_from_url(url, resource, org_id, timeout=10):
    """
    Fetches an image from an external URL (spreadsheet-import's Image URL
    column) and saves it the same validated way as a direct upload.

    Accepted trade-off: the initial hostname/IP is validated and pinned (see
    _pinned_dns), but a redirect's target isn't re-validated before it's
    followed - full protection against redirect-based SSRF bypass would need
    a custom transport that checks every hop. Acceptable here since this is
    an operator-driven bulk-import tool sourcing from known manufacturer
    image hosts, not a public/self-serve endpoint.
    """
    if not url or not url.strip():
        return None
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise UploadError(f"Image URL not allowed: {url}")

    safe_ip = _resolve_safe_ip(parsed.hostname)
    if not safe_ip:
        raise UploadError(f"Image URL not allowed: {url}")

    try:
        with _pinned_dns(parsed.hostname, safe_ip):
            resp = requests.get(
                url, timeout=timeout, stream=True,
                headers={'User-Agent': 'BentCrankshaft-ImageImport/1.0'},
            )
    except requests.RequestException as e:
        raise UploadError(f"Couldn't fetch image URL ({e.__class__.__name__}).")

    with resp:
        if resp.status_code >= 400:
            raise UploadError(f"Image URL returned HTTP {resp.status_code}.")

        content_length = resp.headers.get('Content-Length')
        if content_length and int(content_length) > MAX_IMAGE_BYTES:
            raise UploadError("Image at that URL is too large.")

        data = resp.raw.read(MAX_IMAGE_BYTES + 1, decode_content=True)
        if len(data) > MAX_IMAGE_BYTES:
            raise UploadError("Image at that URL is too large.")

    return _validate_and_save_bytes(data, resource, org_id)
