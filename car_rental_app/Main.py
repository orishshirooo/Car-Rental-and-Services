#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication

# Import the main application window and stylesheet from our 'src' package
from src.app import RentalApp
from src.utils import FORMAL_LIGHT_STYLESHEET

if __name__ == "__main__":
    try:
        # Set the backend for matplotlib to work with PyQt
        plt.switch_backend('QtAgg')

        app = QApplication(sys.argv)

        # Set the global stylesheet
        app.setStyleSheet(FORMAL_LIGHT_STYLESHEET)

        # Create and show the main window
        window = RentalApp()
        window.show()

        sys.exit(app.exec())

    except ImportError as e:
        print(f"A required library is missing ({e}).")
        print("Please install the dependencies from requirements.txt")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"An application error occurred: {e}")
        # In a real app, you might log this to a file
        sys.exit(1)