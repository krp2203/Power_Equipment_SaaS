import os
import uuid
from io import BytesIO

from flask import current_app
from PIL import Image
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8MB


class UploadError(ValueError):
    """Raised when an uploaded file fails validation. The message is safe to
    show directly to the user (flash message / JSON error)."""


def save_image_upload(file_storage, resource, org_id):
    """
    Validates and saves an uploaded image to static/uploads/<resource>/<org_id>/,
    returning its public URL.

    Neither the filename's extension nor the browser-supplied Content-Type is
    trusted on its own - this only accepts an allow-listed extension, enforces
    a size cap, and actually decodes the file with Pillow to confirm it's a
    real, undamaged image before it's ever written to the public static
    directory. Raises UploadError (with a user-facing message) on failure.
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
    try:
        Image.open(BytesIO(data)).verify()
    except Exception:
        raise UploadError("That file doesn't look like a valid image.")

    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', resource, str(org_id))
    os.makedirs(upload_dir, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_storage.save(os.path.join(upload_dir, unique_filename))
    return f"/static/uploads/{resource}/{org_id}/{unique_filename}"
