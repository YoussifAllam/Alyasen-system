import os
import sqlite3
import tempfile
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse


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

    try:
        with open(tmp_path, "rb") as backup_file:
            data = backup_file.read()
    finally:
        os.unlink(tmp_path)

    filename = f"db-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.sqlite3"
    response = HttpResponse(data, content_type="application/x-sqlite3")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Content-Length"] = len(data)
    return response
