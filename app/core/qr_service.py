"""Generate a QR-code PNG for an invoice payment option."""
import os
import uuid

import segno
from flask import current_app


def _dir(org_id):
    d = os.path.join(current_app.root_path, 'static', 'uploads', 'invoice_qr', str(org_id))
    os.makedirs(d, exist_ok=True)
    return d


def generate_qr(org_id, data, *, replace_url=None):
    """Render `data` (a URL/string) to a PNG under static/uploads/invoice_qr/<org>/.
    Deletes `replace_url` (a previously stored /static/... path) if given.
    Returns the new /static/... URL."""
    if replace_url:
        delete_qr(replace_url)
    name = f"{uuid.uuid4().hex}.png"
    path = os.path.join(_dir(org_id), name)
    segno.make(data, error='m').save(path, scale=6, border=2)
    return f"/static/uploads/invoice_qr/{org_id}/{name}"


def delete_qr(static_url):
    """Remove a stored QR/uploaded image by its /static/... URL (best effort)."""
    if not static_url or not static_url.startswith('/static/'):
        return
    path = os.path.join(current_app.root_path, static_url.lstrip('/'))
    try:
        os.remove(path)
    except OSError:
        pass
