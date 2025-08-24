import os
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
    Signal,
    Slot,
)

from src.utilities import SearchRecord, truncate_line

# ----------------------------
# Model (search logic)
# ----------------------------


class SearchModel:
    def __init__(self) -> None:
        pass

    def search_in_file(
        self, filepath: str, needle: str
    ) -> list[tuple[int, int, str]]:
        """Return list of tuples (count_in_line, line_number, line_text)."""
        results = []
        search_lower = needle.lower()
        try:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, start=1):
                    ll = line.lower()
                    if search_lower in ll:
                        count = ll.count(search_lower)
                        results.append((count, i, truncate_line(line)))
        except Exception as e:
            # Ignore unreadable files
            print(f"Warning: could not read file {filepath}: {e}")
        return results

    def recursive_search(
        self,
        folder: str,
        text: str,
        extensions: list[str],
        include_name_matches: bool,
        progress_cb: Callable[[int], None] | None = None,
        stop_flag: Callable[[], bool] = lambda: False,
    ) -> list[SearchRecord]:
        records: list[SearchRecord] = []
        needle_lower = text.lower()

        total_files = 0
        for _, _, files in os.walk(folder):
            total_files += len(files)
        processed = 0

        for root, _, files in os.walk(folder):
            if stop_flag():
                break
            for fname in files:
                if stop_flag():
                    break
                full_path = os.path.join(root, fname)
                fl = fname.lower()

                # 1) filename match
                if include_name_matches and needle_lower in fl:
                    records.append(
                        SearchRecord(
                            occurrences=fl.count(needle_lower),
                            file=full_path,
                            line_number=None,
                            line_text=f"[MATCH IN FILE NAME] {fname}",
                        )
                    )

                # 2) extension and contents
                if any(fl.endswith(ext) for ext in extensions):
                    for count, line_num, line_text in self.search_in_file(
                        full_path, text
                    ):
                        records.append(
                            SearchRecord(
                                occurrences=count,
                                file=full_path,
                                line_number=line_num,
                                line_text=line_text,
                            )
                        )

                processed += 1
                if progress_cb and total_files:
                    pct = int((processed / total_files) * 100)
                    progress_cb(pct)

        return records


# ----------------------------
# Table model (View Model)
# ----------------------------


class ResultsTableModel(QAbstractTableModel):
    HEADERS = ["Occurrences #", "File", "Line #", "Line text"]

    def __init__(self, data: list[SearchRecord] | None = None):
        super().__init__()
        self._data: list[SearchRecord] = data or []

    def setDataSet(self, data: list[SearchRecord]) -> None:  # noqa: N802
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def rowCount(  # noqa: N802
        self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> int:
        return len(self._data)

    def columnCount(  # noqa: N802
        self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> int:
        return 4

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid():
            return None
        rec = self._data[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return rec.occurrences
            elif col == 1:
                return rec.file
            elif col == 2:
                return "-" if rec.line_number is None else rec.line_number
            elif col == 3:
                return rec.line_text
        if role == Qt.ItemDataRole.ToolTipRole and col == 1:
            return rec.file
        return None

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return self.HEADERS[section]
        return super().headerData(section, orientation, role)

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

    def record_at(self, row: int) -> SearchRecord:
        return self._data[row]


# ----------------------------
# Background worker (Thread)
# ----------------------------


class SearchWorker(QObject):
    progress = Signal(int)  # 0..100
    finished = Signal(list)  # list[SearchRecord]
    error = Signal(str)

    def __init__(
        self,
        folder: str,
        text: str,
        extensions: list[str],
        include_names: bool,
    ):
        super().__init__()
        self.folder = folder
        self.text = text
        self.extensions = extensions
        self.include_names = include_names
        self._stop = False
        self.model = SearchModel()

    @Slot()
    def run(self) -> None:
        try:
            results = self.model.recursive_search(
                self.folder,
                self.text,
                self.extensions,
                self.include_names,
                progress_cb=self.progress.emit,
                stop_flag=lambda: self._stop,
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

    def stop(self) -> None:
        self._stop = True
