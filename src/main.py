import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from utilities import resource_path
from view import MainWindow

# ----------------------------
# Main entry
# ----------------------------


def main() -> None:
    logo = resource_path("data/img/icon.png")
    app = QApplication(sys.argv)
    app.setApplicationName("FFinder")
    app.setWindowIcon(QIcon(logo))
    app.setStyle("Fusion")
    w = MainWindow(logo)
    w.show()
    sys.exit(app.exec())
