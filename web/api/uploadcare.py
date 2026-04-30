"""Uploadcare upload helper.

Used to push generated MDs and the bundled .zip back to Uploadcare so the
frontend can hand Scott persistent shareable CDN links.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from pyuploadcare import Uploadcare


_client: Uploadcare | None = None


def _get_client() -> Uploadcare:
    global _client
    if _client is None:
        public_key = os.environ.get("UPLOADCARE_PUBLIC_KEY")
        secret_key = os.environ.get("UPLOADCARE_SECRET_KEY")
        cdn_base = os.environ.get("UPLOADCARE_CDN_BASE")
        if not public_key or not secret_key:
            raise RuntimeError(
                "UPLOADCARE_PUBLIC_KEY and UPLOADCARE_SECRET_KEY must be set in .env."
            )
        kwargs: dict = {"public_key": public_key, "secret_key": secret_key}
        if cdn_base:
            # pyuploadcare concatenates `cdn_base + uuid + '/'` without inserting
            # a separator, so the base must end in '/'.
            kwargs["cdn_base"] = cdn_base.rstrip("/") + "/"
        _client = Uploadcare(**kwargs)
    return _client


def upload_bytes(content: bytes, filename: str) -> str:
    """Upload in-memory bytes to Uploadcare under the given filename.

    pyuploadcare's `client.upload(file_obj)` calls `os.fstat(file_obj.fileno())`,
    which fails on BytesIO — so we write to a temp file with the desired name
    and upload that path.
    """
    client = _get_client()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / filename
        path.write_bytes(content)
        with open(path, "rb") as f:
            uploaded = client.upload(f)
    return uploaded.cdn_url
