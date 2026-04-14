import requests
import os
import sys
import subprocess
from PyQt5.QtWidgets import QMessageBox
from components.Main_Ui_Components.constant import APP_VERSION, BACKEND_BASE_URL


class UpdateManager:
    VERSION_CHECK_URL = f"{BACKEND_BASE_URL}/app-version/version-check/"

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
            # Show a message that download is starting
            progress_msg = QMessageBox(parent)
            progress_msg.setWindowTitle("جاري التحميل")
            progress_msg.setText("بدأ تحميل التحديث، يرجى الانتظار...")
            progress_msg.setStandardButtons(QMessageBox.NoButton)
            progress_msg.show()

            # Download the setup file
            response = requests.get(url, stream=True)
            filename = "Alyasen_Setup.exe"
            temp_path = os.path.join(os.environ.get("TEMP", "/tmp"), filename)

            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

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
