# app/__init__.py
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QGuiApplication

# Function to be called by forgeyt.py
def start_app():
    """Initializes and runs the ForgeYT Qt application."""

    # --- Import Main Window and Version ---
    # Import necessary components here to avoid circular imports if possible
    # and to keep the initial forgeyt.py lighter.
    try:
        from .main_window import App # Import the main UI class
        from utils import CURRENT_VERSION # Import version from utils package
    except ImportError as e:
         print(f"Fatal Error: Could not import App or CURRENT_VERSION in app/__init__.py: {e}", file=sys.stderr)
         print("Ensure main_window.py and the utils package exist and are correct.", file=sys.stderr)
         sys.exit(1)
    except Exception as e:
        print(f"Fatal Error during import in app/__init__.py: {e}", file=sys.stderr)
        sys.exit(1)


    # --- Configure Qt Application Settings ---
    # Set High DPI attributes BEFORE creating QApplication
    try: QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    except AttributeError: print("Warning: Qt.AA_EnableHighDpiScaling not available.")
    #try: QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    try: QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.RoundPreferFloor)
    except AttributeError: print("Warning: setHighDpiScaleFactorRoundingPolicy not available.")

    # Set application info (optional)
    QCoreApplication.setApplicationName("ForgeYT")
    QCoreApplication.setOrganizationName("ForgedCore") # Optional
    QCoreApplication.setApplicationVersion(CURRENT_VERSION)

    # --- Create and Run Application ---
    app = QApplication(sys.argv)
    window = App() # Instantiate the main window
    window.show()
    sys.exit(app.exec()) # Start the Qt event loop

# Expose start_app for import 'from app import start_app'
__all__ = ['start_app']