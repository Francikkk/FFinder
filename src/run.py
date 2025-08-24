import sys

from PySide6.QtWidgets import QApplication

from src.view import MainWindow

# ----------------------------
# Main entry
# ----------------------------


def main() -> None:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
