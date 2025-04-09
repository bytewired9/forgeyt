# app/messagebox.py
from PySide6.QtWidgets import QMessageBox, QPushButton
from PySide6.QtGui import QIcon, QPixmap, QPalette
from PySide6.QtCore import Qt

# Import UI constants
from .ui_constants import (
    C_BTN_LIGHT, C_BTN_DARK, C_BTN_HOVER_LIGHT, C_BTN_HOVER_DARK,
    C_BG_LIGHT_1, C_BG_DARK_1, C_TEXT_LIGHT, C_TEXT_DARK
)

class CustomMessageBox(QMessageBox):
    """
    A custom message box example that applies light or dark styling based
    on an explicit mode setting on the parent widget (if available), or falls
    back to inspecting the parent's palette.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    @staticmethod
    def show_message(parent, title, message, btn_color=None, btn_hover=None, icon=QMessageBox.Icon.Information):
        msgBox = CustomMessageBox(parent)
        msgBox.setWindowTitle(title)
        msgBox.setText(message)

        # Set the icon type
        if icon == QMessageBox.Icon.Information:
            msgBox.setIcon(QMessageBox.Icon.Information)
        elif icon == QMessageBox.Icon.Warning:
            msgBox.setIcon(QMessageBox.Icon.Warning)
        elif icon == QMessageBox.Icon.Critical:
            msgBox.setIcon(QMessageBox.Icon.Critical)
        elif icon == QMessageBox.Icon.Question:
            msgBox.setIcon(QMessageBox.Icon.Question)

        # Check for an explicit mode on the parent, otherwise use the parent's palette
        if parent is not None and hasattr(parent, "_is_dark_mode"):
            is_dark = parent._is_dark_mode
        else:
            is_dark = False
            try:
                palette = parent.palette()
                # Use the lightness of the window color to decide
                is_dark = palette.window().color().lightness() < 128
            except Exception:
                pass

        # If button colors are not provided, select defaults based on mode
        if btn_color is None:
            btn_color = C_BTN_DARK if is_dark else C_BTN_LIGHT
        if btn_hover is None:
            btn_hover = C_BTN_HOVER_DARK if is_dark else C_BTN_HOVER_LIGHT

        # Set overall background and text colors based on the detected mode
        bg_color = C_BG_DARK_1 if is_dark else C_BG_LIGHT_1
        text_color = C_TEXT_DARK if is_dark else C_TEXT_LIGHT

        # Add a standard OK button
        msgBox.addButton(QMessageBox.StandardButton.Ok)

        # Apply a stylesheet that affects both the overall message box and its buttons
        style = f"""
        QMessageBox {{
            background-color: {bg_color};
            color: {text_color};
        }}
        QPushButton {{
            background-color: {btn_color};
            color: white;
            border: none;
            padding: 8px 18px;
            border-radius: 5px;
            min-height: 28px;
            font-size: 10pt;
        }}
        QPushButton:hover {{
            background-color: {btn_hover};
        }}
        """
        msgBox.setStyleSheet(style)
        msgBox.exec()
