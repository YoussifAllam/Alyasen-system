import os
import sqlite3
import tempfile
from datetime import datetime

from django.conf import settings
from django.http import FileResponse


class _TempFileResponse(FileResponse):
    """FileResponse that removes the temp backup file when the stream closes."""

    def __init__(self, temp_path: str, *args, **kwargs):
        self._temp_path = temp_path
        super().__init__(open(temp_path, "rb"), *args, **kwargs)

    def close(self):
        super().close()
        try:
            os.unlink(self._temp_path)
        except OSError:
            pass


def build_sqlite_backup_response():
    engine = settings.DATABASES["default"]["ENGINE"]
    if "sqlite3" not in engine:
        raise ValueError("النسخ الاحتياطي متاح فقط عند استخدام SQLite على الخادم")

    db_path = settings.DATABASES["default"]["NAME"]
    if not os.path.isfile(db_path):
        raise FileNotFoundError("ملف قاعدة البيانات غير موجود على الخادم")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3")
    tmp_path = tmp.name
    tmp.close()

    src_conn = sqlite3.connect(db_path, timeout=30)
    dest_conn = sqlite3.connect(tmp_path)
    try:
        with dest_conn:
            src_conn.backup(dest_conn)
    finally:
        src_conn.close()
        dest_conn.close()

    filename = f"db-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.sqlite3"
    return _TempFileResponse(
        tmp_path,
        as_attachment=True,
        filename=filename,
        content_type="application/x-sqlite3",
    )
