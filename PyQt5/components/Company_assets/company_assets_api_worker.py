from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from requests import exceptions, request


class MachineApiWorker(QObject):
    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, method, url, payload=None, files=None):
        super().__init__()
        self.method = method
        self.url = url
        self.payload = payload
        self.files = files

    @pyqtSlot()
    def run(self):
        try:
            if self.method == "POST" and self.files:
                response = request(
                    self.method,
                    self.url,
                    data=self.payload,
                    files=self.files,
                    timeout=8,
                )
            elif self.method == "DELETE":
                response = request(
                    self.method, self.url, json=self.payload, timeout=8
                )
            else:
                kwargs = {"timeout": 8}
                if self.payload is not None:
                    kwargs["json"] = self.payload
                response = request(self.method, self.url, **kwargs)
            if response.status_code in (200, 201, 204):
                if response.status_code == 204:
                    self.success.emit({})
                else:
                    self.success.emit(response.json())
            else:
                try:
                    error_data = response.json()
                    if "errors" in error_data:
                        error_msg = error_data["errors"]
                    elif "الخطاء" in error_data:
                        error_msg = error_data["الخطاء"]
                    elif "error" in error_data:
                        error_msg = error_data["error"]
                    else:
                        error_msg = next(
                            iter(error_data.values()), f"HTTP {response.status_code}"
                        )
                    if isinstance(error_msg, dict):
                        error_msg = next(iter(error_msg.values()))
                    if isinstance(error_msg, list):
                        error_msg = error_msg[0]
                    self.error.emit(str(error_msg))
                except Exception:
                    self.error.emit(
                        response.text or f"خطأ من الخادم: {response.status_code}"
                    )
        except exceptions.RequestException as e:
            self.error.emit(f"فشل الاتصال بالخادم: {e}")
        finally:
            if self.files:
                for entry in self.files:
                    file_obj = entry[1]
                    if isinstance(file_obj, tuple):
                        file_obj = file_obj[1]
                    if hasattr(file_obj, "close"):
                        file_obj.close()
            self.finished.emit()
