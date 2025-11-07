import os

from PySide6.QtCore import QObject, QThread, Signal

from .model import SearchWorker
from .utilities import SearchRecord, sanitize_extensions

# ----------------------------
# Controller
# ----------------------------


class SearchController(QObject):
    scanningChanged = Signal(bool)  # noqa: N815
    resultsReady = Signal(list)  # noqa: N815
    progressChanged = Signal(int)  # noqa: N815
    errorOccurred = Signal(str)  # noqa: N815

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self.worker: SearchWorker | None = None

    def validate_inputs(self, folder: str, needle: str) -> str | None:
        if not folder:
            return "Please choose a folder."
        if not os.path.isdir(folder):
            return "The selected path is not a directory."
        if not needle:
            return "Please enter the text to search for."
        return None

    def start_scan(
        self, folder: str, needle: str, ext_text: str, include_names: bool
    ) -> None:
        err = self.validate_inputs(folder, needle)
        if err:
            self.errorOccurred.emit(err)
            return

        extensions = sanitize_extensions(ext_text)
        self.stop_scan()  # in case something is running

        self._thread = QThread()
        self.worker = SearchWorker(folder, needle, extensions, include_names)
        self.worker.moveToThread(self._thread)

        self._thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progressChanged)
        self.worker.error.connect(self._on_worker_error)
        self.worker.finished.connect(self._on_worker_finished)

        self._thread.finished.connect(self._thread.deleteLater)
        self.scanningChanged.emit(True)
        self._thread.start()

    def _on_worker_error(self, msg: str) -> None:
        self.errorOccurred.emit(msg)
        self.scanningChanged.emit(False)
        self.stop_scan()

    def _on_worker_finished(self, results: list[SearchRecord]) -> None:
        self.resultsReady.emit(results)
        self.scanningChanged.emit(False)
        self.stop_scan()

    def stop_scan(self) -> None:
        if self.worker:
            self.worker.stop()
            self.worker = None
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
