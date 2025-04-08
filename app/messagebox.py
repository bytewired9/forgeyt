# app/messagebox.py
from PySide6.QtWidgets import QMessageBox, QPushButton
from PySide6.QtGui import QIcon, QPixmap

class CustomMessageBox(QMessageBox):
    """
    A custom message box example allowing styled buttons.
    Replace with your actual implementation.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    @staticmethod
    def show_message(parent, title, message, btn_color="#C83232", btn_hover="#970222", icon=QMessageBox.Icon.Information):
        msgBox = CustomMessageBox(parent)
        msgBox.setWindowTitle(title)
        msgBox.setText(message)

        # Set standard icon
        if icon == QMessageBox.Icon.Information:
            msgBox.setIcon(QMessageBox.Icon.Information)
        elif icon == QMessageBox.Icon.Warning:
            msgBox.setIcon(QMessageBox.Icon.Warning)
        elif icon == QMessageBox.Icon.Critical:
            msgBox.setIcon(QMessageBox.Icon.Critical)
        elif icon == QMessageBox.Icon.Question:
             msgBox.setIcon(QMessageBox.Icon.Question)
        # Add other icon types if needed

        # Add standard buttons (e.g., OK)
        okButton = msgBox.addButton(QMessageBox.StandardButton.Ok)

        # Apply basic styling (more complex styling might require QProxyStyle)
        # Note: This hover effect requires event filtering or a custom button class
        # for full reliability within QMessageBox. This is a simplified example.
        style = f"""
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