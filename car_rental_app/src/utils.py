import sys
import os
import hashlib
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt

# --- STYLESHEET ---
FORMAL_LIGHT_STYLESHEET = """
    /* ----- Palette (FORMAL LIGHT) ----- */
    /*
    --bg-main: #f4f4f4;        /* Light grey app background */
    --bg-content: #ffffff;     /* White for content areas */
    --border: #cccccc;         /* Standard grey border */
    --text-main: #333333;      /* Dark charcoal text */
    --text-light: #555555;     /* Lighter grey text */
    --primary: #0078d4;        /* Professional blue (accent) */
    --primary-hover: #005a9e;  /* Darker blue */
    --danger: #e74c3c;
    --danger-hover: #c0392b;
    --secondary: #6c757d;      /* Standard grey button */
    --secondary-hover: #5a6268;
    */

    /* ----- Global Defaults ----- */
    QWidget {
        background-color: #f4f4f4;
        color: #333333;
    }

    /* ----- Text & Labels ----- */
    QLabel, QCheckBox {
        font-size: 10pt;
        background-color: transparent;
        color: #333333;
    }

    /* Make links in QLabels blue */
    QLabel a {
        color: #0078d4;
    }

    /* ----- Input Fields ----- */
    QLineEdit, QTextEdit, QComboBox {
        background-color: #ffffff;
        color: #333333;
        padding: 8px;
        border: 1px solid #cccccc;
        border-radius: 4px;
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
        border: 1px solid #0078d4; 
    }
    QLineEdit:read-only {
        background-color: #eeeeee;
    }

    /* Style QComboBox dropdown */
    QComboBox::drop-down {
        border: none;
    }
    QComboBox::down-arrow {
        image: url(down_arrow_dark.png); /* You might need a dark arrow icon */
    }
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #cccccc;
        selection-background-color: #0078d4;
        selection-color: white;
    }


    /* ----- Content Areas ----- */
    QGroupBox {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 5px;
        margin-top: 10px;
        padding: 15px;
        font-size: 10pt;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 10px;
        color: #555555;
        font-weight: bold;
    }

    QScrollArea {
        border: none;
        background-color: #ffffff;
    }
    QScrollArea > QWidget > QWidget {
         background-color: #ffffff;
    }

    /* --- Dialogs --- */
    QDialog {
        background-color: #f4f4f4;
    }
    QDialog QLineEdit, QDialog QComboBox {
        padding: 5px;
    }

    /* ----- Tables ----- */
    QTableWidget {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        gridline-color: #cccccc;
        color: #333333;
    }
    QHeaderView::section {
        background-color: #f4f4f4;
        padding: 5px;
        border-bottom: 2px solid #0078d4;
        border-right: 1px solid #cccccc;
        font-weight: bold;
        color: #555555;
    }

    /* ----- Buttons ----- */
    QPushButton {
        background-color: #0078d4;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px;
        font-size: 10pt;
        font-weight: bold;

    }
    QPushButton:hover {
        background-color: #005a9e;
    }

    /* ----- Special Buttons (by objectName) ----- */
    QPushButton#DangerButton {
        background-color: #e74c3c;
    }
    QPushButton#DangerButton:hover {
        background-color: #c0392b;
    }

    QPushButton#SecondaryButton {
        background-color: #6c757d;
        color: white;
        font-size: 9pt;
        padding: 5px 8px;
        font-weight: normal;
    }
    QPushButton#SecondaryButton:hover {
        background-color: #5a6268;
    }

    /* ----- Sidebar (by objectName) ----- */
    QWidget#Sidebar {
        background-color: #ffffff;
        border-right: 1px solid #cccccc;
    }
    QWidget#Sidebar QLabel {
        color: #0078d4;
        font-weight: bold;
        font-size: 11pt;
        background-color: transparent;
    }
    QWidget#Sidebar QPushButton {
        background-color: transparent;
        color: #555555;
        padding: 12px 10px;
        border: none;
        text-align: left;
        margin: 5px 10px;
        border-radius: 4px;
        font-weight: bold;
    }
    QWidget#Sidebar QPushButton:hover {
        background-color: #eaf6ff;
        color: #005a9e;
    }
"""

# --- Helper function for finding asset files ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# --- Utility Functions ---

def hash_password(password):
    """Hashes the password using SHA256 for secure storage."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def format_peso(amount):
    return f"₱{amount:,.2f}"

def load_pixmap(filename, width=None, height=None):
    """Helper to load a QPixmap from a resource path."""
    try:
        pixmap = QPixmap(resource_path(filename))
        if width and height:
            return pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        return pixmap
    except Exception:
        return QPixmap() # Return an empty pixmap on failure

def load_icon(filename):
    """Helper to load a QIcon from a resource path."""
    try:
        return QIcon(resource_path(filename))
    except Exception:
        return QIcon() # Return an empty icon on failure