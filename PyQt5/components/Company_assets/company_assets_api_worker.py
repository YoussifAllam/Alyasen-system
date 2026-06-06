from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from requests import exceptions, request

from ..utils.api_errors import format_request_exception, parse_api_response


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
            ok, result = parse_api_response(response)
            if ok:
                self.success.emit(result if isinstance(result, dict) else {})
            else:
                self.error.emit(result)
        except exceptions.RequestException as e:
            self.error.emit(format_request_exception(e))
        finally:
            if self.files:
                for entry in self.files:
                    file_obj = entry[1]
                    if isinstance(file_obj, tuple):
                        file_obj = file_obj[1]
                    if hasattr(file_obj, "close"):
                        file_obj.close()
            self.finished.emit()
