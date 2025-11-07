import os
import platform
import subprocess
import sys
from dataclasses import dataclass

# ----------------------------
# Constants
# ----------------------------


DEFAULT_EXTENSIONS = [
    ".config",
    ".conf",
    ".xml",
    ".json",
    ".ini",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",
    ".txt",
    ".log",
    ".md",
    ".csv",
]


# ----------------------------
# Constants
# ----------------------------


def resource_path(relative_path: str) -> str:
    """
    Get absolute path to a resource, works in development and
    PyInstaller-built exe.
    """
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


# ----------------------------
# Data structures
# ----------------------------


@dataclass
class SearchRecord:
    occurrences: int
    file: str
    line_number: int | None  # None means "match in filename"
    line_text: str


# ----------------------------
# Utilities (shared by MVC)
# ----------------------------


def sanitize_extensions(input_str: str) -> list[str]:
    """
    Parse the user's combobox text. Accepts CSV of extensions (with or without
    dots).
    Accepts '*' to mean DEFAULT_EXTENSIONS (safer than "everything" for
    performance).
    """
    text = (input_str or "").strip()
    if not text:
        return DEFAULT_EXTENSIONS
    if text == "*":
        return DEFAULT_EXTENSIONS
    parts = [p.strip() for p in text.split(",") if p.strip()]
    ext_list = []
    for ext in parts:
        if not ext.startswith("."):
            ext = "." + ext
        ext_list.append(ext.lower())
    return ext_list or DEFAULT_EXTENSIONS


def truncate_line(s: str, limit: int = 90) -> str:
    s = s.rstrip("\n\r")
    if len(s) <= limit:
        return s
    return s[: limit - 3] + "..."


def open_in_file_manager_select(path: str) -> None:
    """
    Open the containing folder and select/highlight the file when supported.
    Windows: explorer /select,
    macOS:   open -R
    Linux:   best-effort open folder (selection depends on file manager;
    not guaranteed)
    """
    system = platform.system()
    if system == "Windows":
        subprocess.Popen(  # noqa S607
            ["explorer", "/select,", os.path.normpath(path)]  # noqa S607
        )
    elif system == "Darwin":
        subprocess.Popen(["open", "-R", path])  # noqa S607
    else:
        # Linux/Unix: try to select with common FMs; if not, open the folder.
        folder = os.path.dirname(path)
        # Try nautilus --select if available
        try:
            subprocess.Popen(["nautilus", "--select", path])  # noqa S607
            return
        except Exception as e:
            print(f"Error opening nautilus: {e}")
        # Fallback: just open folder
        try:
            subprocess.Popen(["xdg-open", folder])  # noqa S607
        except Exception as e:
            print(f"Error opening xdg-open: {e}")
