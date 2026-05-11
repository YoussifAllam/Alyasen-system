import requests
import os
import sys
import subprocess
import re
from urllib.parse import urlparse, parse_qs
from PyQt5.QtWidgets import QMessageBox
from components.Main_Ui_Components.constant import APP_VERSION, BACKEND_BASE_URL


class UpdateManager:
    VERSION_CHECK_URL = f"{BACKEND_BASE_URL}/app-version/version-check/"

    @staticmethod
    def _normalize_drive_url(url: str) -> str:
        """
        Accepts Google Drive share links and converts them to a download URL.
        Supports:
          - https://drive.google.com/file/d/<ID>/view?...
          - https://drive.google.com/open?id=<ID>
          - https://drive.google.com/uc?id=<ID>&export=download
        """
        if not url:
            return url

        parsed = urlparse(url)
        if "drive.google.com" not in parsed.netloc:
            return url

        # /file/d/<id>/view
        m = re.search(r"/file/d/([^/]+)/", parsed.path)
        file_id = m.group(1) if m else None

        # open?id=<id> or uc?id=<id>
        if not file_id:
            qs = parse_qs(parsed.query)
            if "id" in qs and qs["id"]:
                file_id = qs["id"][0]

        if not file_id:
            return url

        return f"https://drive.google.com/uc?export=download&id={file_id}"

    @staticmethod
    def _download_file(url: str, dest_path: str, timeout: int = 30):
        """
        Downloads a file. If the URL is a Google Drive link and requires confirmation,
        it will retry with the confirmation token.
        """
        session = requests.Session()
        session.headers.update({"User-Agent": "AlyasenCRM-Updater/1.0"})

        url = UpdateManager._normalize_drive_url(url)
        resp = session.get(url, stream=True, timeout=timeout, allow_redirects=True)

        # Google Drive large file confirmation flow
        if "drive.google.com" in urlparse(resp.url).netloc and "text/html" in (
            resp.headers.get("Content-Type", "")
        ):
            confirm = None
            for k, v in resp.cookies.items():
                if k.startswith("download_warning"):
                    confirm = v
                    break
            if confirm:
                sep = "&" if "?" in url else "?"
                url2 = f"{url}{sep}confirm={confirm}"
                resp = session.get(
                    url2, stream=True, timeout=timeout, allow_redirects=True
                )

        resp.raise_for_status()

        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)

    @staticmethod
    def check_for_updates(parent=None):
        try:
            response = requests.get(UpdateManager.VERSION_CHECK_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("version")
                download_url = data.get("url")
                update_notes = data.get("notes", "")

                if latest_version and latest_version != APP_VERSION:
                    msg_box = QMessageBox(parent)
                    msg_box.setWindowTitle("تحديث جديد متوفر")
                    msg_box.setText(f"تم العثور على إصدار جديد: {latest_version}")
                    msg_box.setInformativeText(
                        f"الملاحظات: {update_notes}\n\nهل ترغب في التحديث الآن؟"
                    )
                    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    msg_box.setDefaultButton(QMessageBox.Yes)
                    msg_box.setIcon(QMessageBox.Information)

                    if msg_box.exec_() == QMessageBox.Yes:
                        UpdateManager.download_and_install(download_url, parent)
        except Exception as e:
            print(f"Error checking for updates: {e}")

    @staticmethod
    def download_and_install(url, parent=None):
        try:
            if not url:
                QMessageBox.critical(parent, "خطأ", "رابط التحميل غير متوفر.")
                return

            # Show a message that download is starting
            progress_msg = QMessageBox(parent)
            progress_msg.setWindowTitle("جاري التحميل")
            progress_msg.setText("بدأ تحميل التحديث، يرجى الانتظار...")
            progress_msg.setStandardButtons(QMessageBox.NoButton)
            progress_msg.show()

            # Download the setup file
            filename = "Alyasen_Setup.exe"
            temp_path = os.path.join(os.environ.get("TEMP", "/tmp"), filename)
            UpdateManager._download_file(url, temp_path, timeout=60)

            progress_msg.close()

            # Run the installer and exit the app
            # Inno Setup installers can be run with /SILENT or /VERYSILENT for auto-update
            # But usually we just run it normally so user can confirm.
            subprocess.Popen([temp_path, "/SILENT"])
            sys.exit(0)

        except Exception as e:
            QMessageBox.critical(
                parent, "خطأ في التحديث", f"حدث خطأ أثناء تحميل التحديث: {e}"
            )
