import os

from PySide6.QtCore import QModelIndex, Slot
from PySide6.QtGui import QIcon, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from controller import SearchController
from model import ResultsTableModel
from utilities import SearchRecord, open_in_file_manager_select

# ----------------------------
# View
# ----------------------------


class MainWindow(QMainWindow):
    def __init__(self, logo_path: str) -> None:
        super().__init__()
        self.setWindowTitle("FFinder")
        self.setWindowIcon(QIcon(logo_path))
        self.resize(1100, 700)

        # Controller + Model for table
        self.controller = SearchController()
        self.table_model = ResultsTableModel([])

        # Bind controller signals
        self.controller.scanningChanged.connect(self.on_scanning_changed)
        self.controller.resultsReady.connect(self.on_results_ready)
        self.controller.progressChanged.connect(self.on_progress_changed)
        self.controller.errorOccurred.connect(self.on_error)

        # Build UI
        central = QWidget(self)
        self.setCentralWidget(central)
        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)
        menu_bar.setVisible(False)  # Remove the default (empty) menu bar
        root_layout = QVBoxLayout(central)

        # Top input group
        inputs_group = QGroupBox("Search Parameters", self)
        inputs_layout = QGridLayout(inputs_group)

        self.path_edit = QLineEdit(self)
        self.path_btn = QPushButton("Browse…", self)
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Text to find…")
        self.ext_combo = QComboBox(self)
        self.ext_combo.setEditable(True)
        self.ext_combo.addItems(
            [
                "txt",
                "log",
                "xml",
                "json",
                "ini",
                "yaml,yml",
                "toml",
                "cfg,",
                "conf",
                "csv",
                "md",
                "*",
            ]
        )
        self.ext_combo.setCurrentIndex(
            -1
        )  # keep line edit empty for placeholder
        self.ext_combo.lineEdit().setPlaceholderText(
            "e.g. txt,log,json or * for all the supported types"
        )
        self.include_names_check = QCheckBox(
            "Include matches from file names", self
        )
        self.include_names_check.setChecked(True)

        self.start_btn = QPushButton("Start Scan", self)
        self.status_label = QLabel("", self)

        inputs_layout.addWidget(QLabel("Path:"), 0, 0)
        inputs_layout.addWidget(self.path_edit, 0, 1)
        inputs_layout.addWidget(self.path_btn, 0, 2)

        inputs_layout.addWidget(QLabel("Find:"), 1, 0)
        inputs_layout.addWidget(self.search_edit, 1, 1)
        inputs_layout.addWidget(self.start_btn, 1, 2)

        inputs_layout.addWidget(QLabel("File types:"), 2, 0)
        inputs_layout.addWidget(self.ext_combo, 2, 1)
        inputs_layout.addWidget(self.include_names_check, 2, 2)

        inputs_layout.addWidget(self.status_label, 3, 0, 1, 3)

        # Bottom results table
        self.table = QTableView(self)
        self.table.setModel(self.table_model)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.table.doubleClicked.connect(self.on_table_double_clicked)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.table.setSortingEnabled(True)

        root_layout.addWidget(inputs_group)
        root_layout.addWidget(self.table)

        # Actions
        self.path_btn.clicked.connect(self.choose_folder)
        self.start_btn.clicked.connect(self.on_start_clicked)

        # Keep last search text for highlight
        self._last_needle: str = ""

    # ------- Slots / Handlers

    @Slot()
    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Choose folder to scan"
        )
        if folder:
            self.path_edit.setText(folder)

    @Slot()
    def on_start_clicked(self) -> None:
        folder = self.path_edit.text().strip()
        needle = self.search_edit.text().strip()
        ext_text = self.ext_combo.currentText().strip()
        include_names = self.include_names_check.isChecked()

        self._last_needle = needle
        self.controller.start_scan(folder, needle, ext_text, include_names)

    @Slot(bool)
    def on_scanning_changed(self, running: bool) -> None:
        self.start_btn.setEnabled(not running)
        self.path_btn.setEnabled(not running)
        self.path_edit.setEnabled(not running)
        self.search_edit.setEnabled(not running)
        self.ext_combo.setEnabled(not running)
        self.include_names_check.setEnabled(not running)
        self.status_label.setText("Scanning…" if running else "Ready.")

    @Slot(int)
    def on_progress_changed(self, pct: int) -> None:
        self.status_label.setText(f"Scanning… {pct}%")

    @Slot(list)
    def on_results_ready(self, results: list[SearchRecord]) -> None:
        self.table_model.setDataSet(results)
        self.status_label.setText(f"Found {len(results)} matches.")

    @Slot(str)
    def on_error(self, msg: str) -> None:
        QMessageBox.critical(self, "Error", msg)
        self.status_label.setText("Error.")

    @Slot(QModelIndex)
    def on_table_double_clicked(self, index: QModelIndex) -> None:
        if not index.isValid():
            return
        row = index.row()
        rec = self.table_model.record_at(row)
        if rec.line_number is None:
            # filename match -> open folder and select file
            open_in_file_manager_select(rec.file)
        else:
            # text match -> open internal viewer at line
            dlg = FileViewerDialog(
                rec.file, rec.line_number, self._last_needle, self
            )
            dlg.exec()


# ----------------------------
# File viewer dialog
# ----------------------------


class FileViewerDialog(QDialog):
    def __init__(
        self,
        file_path: str,
        goto_line: int | None,
        highlight_text: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Viewer – {os.path.basename(file_path)}")
        self.resize(900, 600)

        layout = QVBoxLayout(self)
        self.editor = QPlainTextEdit(self)
        self.editor.setReadOnly(True)
        layout.addWidget(self.editor)

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                self.editor.setPlainText(f.read())
        except Exception as e:
            self.editor.setPlainText(f"[Error opening file]\n{e}")

        # Jump to line and highlight matches
        if goto_line and goto_line > 0:
            block = self.editor.document().findBlockByNumber(goto_line - 1)
            cursor = QTextCursor(block)
            self.editor.setTextCursor(cursor)
            self.editor.centerCursor()

        if highlight_text:
            self.highlight_all(highlight_text)

    def highlight_all(self, text: str) -> None:
        doc = self.editor.document()
        cursor = QTextCursor(doc)
        cursor.beginEditBlock()
        # selections: list[QTextCursor] = []

        fmt = QTextCharFormat()
        fmt.setBackground(self.palette().highlight())
        fmt.setForeground(self.palette().highlightedText())

        # Find all case-insensitive matches
        start = 0
        plain = self.editor.toPlainText()
        needle = text.lower()
        while True:
            pos = plain.lower().find(needle, start)
            if pos == -1:
                break
            sel = QTextCursor(doc)
            sel.setPosition(pos)
            sel.setPosition(pos + len(text), QTextCursor.MoveMode.KeepAnchor)
            sel.setCharFormat(fmt)
            start = pos + len(text)
        cursor.endEditBlock()
