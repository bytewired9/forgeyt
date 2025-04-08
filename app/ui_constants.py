import base64

# --- Color Palette (Constants) ---
C_BG_LIGHT_1 = "#FAFEFE"
C_BG_DARK_1 = "#04251E"
C_BG_LIGHT_2 = "#F3D3DA"
C_BG_DARK_2 = "#031B16"
C_BTN_LIGHT = "#D21941"
C_BTN_DARK = "#C83232"
C_BTN_HOVER_LIGHT = "#841029"
C_BTN_HOVER_DARK = "#970222"
C_TEXT_LIGHT = "#000000"
C_TEXT_DARK = "#FFFFFF"
C_INPUT_BORDER_LIGHT = "#AAAAAA"
C_INPUT_BORDER_DARK = "#555555"
C_THEME_BTN_UNCHECKED_BG_LIGHT = "#DDDDDD"
C_THEME_BTN_UNCHECKED_BG_DARK = "#555555"
C_SCROLLBAR_BG_LIGHT = C_BG_LIGHT_1
C_SCROLLBAR_BG_DARK = C_BG_DARK_1
C_SCROLLBAR_HANDLE = "#888888"
C_CONSOLE_BG_LIGHT = "#E8E8E8"
C_CONSOLE_BG_DARK = C_BG_DARK_2  # Match dark left frame

# --- Style Values (Constants) ---
S_BORDER_RADIUS = "8px"
S_INPUT_BORDER_RADIUS = "6px"
S_NAV_BUTTON_PADDING = "12px 16px"
S_NAV_BUTTON_MARGIN = "5px 0"
S_ACTION_BUTTON_PADDING = "10px 20px"
S_FONT_FAMILY = "Segoe UI, sans-serif"
S_FONT_SIZE_DEFAULT = "11pt"
S_FONT_SIZE_TITLE = "26pt"
S_FONT_SIZE_SECTION = "13pt"
S_FONT_SIZE_VERSION = "9pt"
S_CONSOLE_FONT_FAMILY = "Consolas, Courier New, monospace"

# --- Stylesheet Template ---
STYLE_TEMPLATE = """
    QWidget {{
        background: none;
        color: {text};
        font-family: {font_family};
        font-size: {font_size_default};
    }}

    QWidget#leftFrame {{
        background-color: {bg2};
        border-right: 1px solid {input_border};
    }}
    QWidget#rightFrame {{
        background-color: {bg1};
    }}

    /* Navigation Buttons */
    QPushButton#navButton {{
        background-color: {btn};
        color: white;
        border: none;
        padding: {nav_btn_padding};
        margin: {nav_btn_margin};
        border-radius: {border_radius};
        text-align: center;
    }}
    QPushButton#navButton:hover {{
        background-color: {btn_h};
    }}
    QPushButton#navButton:checked {{
        background-color: {btn_h};
        font-weight: bold;
    }}

    /* Action Buttons */
    QPushButton#actionButton,
    QPushButton#selectFolderButton,
    QPushButton#saveButton,
    QPushButton#resetButton,
    QPushButton#ffmpegBrowseButton,
    QPushButton#ffprobeBrowseButton
      {{
        background-color: {btn};
        color: white;
        border: none;
        padding: {action_btn_padding};
        border-radius: {border_radius};
        min-height: 20px;
    }}
    QPushButton#actionButton:hover,
    QPushButton#selectFolderButton:hover,
    QPushButton#saveButton:hover,
    QPushButton#resetButton:hover,
    QPushButton#ffmpegBrowseButton:hover,
    QPushButton#ffprobeBrowseButton:hover {{
        background-color: {btn_h};
    }}
    QPushButton#actionButton:disabled {{
        background-color: #777777;
        color: #AAAAAA;
    }}

    /* Download Button (Start) */
    QPushButton#startButton {{
        background-color: {btn};
        color: white;
        border: none;
        padding: {action_btn_padding};
        border-radius: {border_radius};
        min-width: 80px;
        min-height: 40px;
    }}
    QPushButton#startButton:hover {{
        background-color: {btn_h};
    }}

    QPushButton#cookieButton {{
        background-color: {btn};
        color: white;
        border: none;
        padding: 6px 10px;
        border-radius: {border_radius};
        min-width: 60px;
        min-height: 20px;
    }}
    QPushButton#cookieButton:hover {{
        background-color: {btn_h};
    }}

    /* Specific Buttons */
    QPushButton#stopButton {{
        background-color: #FFA500;
        color: black;
        min-width: 40px;
        min-height: 40px;
    }}
    QPushButton#stopButton:hover {{
        background-color: #E59400;
    }}
    QPushButton#updateButton {{
        background-color: #4CAF50;
        color: white;
        padding: 6px 12px;
        font-size: {font_size_default};
        border-radius: {border_radius};
    }}
    QPushButton#updateButton:hover {{
        background-color: #45a049;
    }}

    /* Labels */
    QLabel#pageTitle {{
        font-size: {font_size_title};
        font-weight: bold;
        text-align: center;
        margin-bottom: 15px;
    }}
    QLabel#sectionTitle {{
        font-size: {font_size_section};
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 5px;
    }}
    QLabel#versionLabel {{
        font-style: italic;
        font-size: {font_size_version};
        color: #888888;
        margin-top: 15px;
        text-align: center;
    }}

    /* Input Widgets */
    QLineEdit,
    QComboBox,
    QTextEdit {{
        background-color: {input_bg};
        color: {text};
        border: 1px solid {input_border};
        border-radius: {input_border_radius};
        padding: 8px;
        font-size: {font_size_default};
    }}
    QLineEdit:focus,
    QComboBox:focus,
    QTextEdit:focus {{
        border: 1px solid {btn};
    }}
    QComboBox::drop-down {{
        border: none;
        background: transparent;
        padding-right: 5px;
    }}
    QComboBox::down-arrow {{
        image: url({arrow_icon_path});
        width: 12px;
        height: 12px;
    }}

    /* CheckBoxes */
    QCheckBox {{
        spacing: 8px;
        font-size: {font_size_default};
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: {input_border_radius};
        background-color: {input_bg};
        border: 1px solid {input_border};
    }}
    QCheckBox::indicator:checked {{
        background-color: {btn};
        border: 1px solid {btn};
    }}
    QCheckBox::indicator:unchecked:hover {{
        border: 1px solid {btn_h};
    }}

    /* Console */
    QTextEdit#consoleOutput {{
        font-family: {console_font_family};
        background-color: {console_bg};
    }}

    /* Progress Bar */
    QProgressBar {{
        border: 1px solid {input_border};
        border-radius: {input_border_radius};
        text-align: center;
        background-color: {input_bg};
        color: {text};
        min-height: 20px;
        width: 80%;
    }}
    QProgressBar::chunk {{
        background-color: {btn};
        border-radius: {input_border_radius};
    }}

    /* Scroll Area */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QWidget#scrollAreaWidgetContents {{
        background-color: transparent;
    }}

    /* Theme Selection Buttons */
    QPushButton#themeButton {{
        padding: 8px 12px;
        font-size: {font_size_default};
        border-radius: {input_border_radius};
        border: 1px solid {input_border};
    }}
    QPushButton#themeButton:checked {{
        background-color: {btn};
        color: white;
        border: 1px solid {btn};
    }}
    QPushButton#themeButton:!checked {{
        background-color: {theme_btn_unchecked_bg};
        color: {theme_btn_unchecked_text};
        border: 1px solid {input_border};
    }}
    QPushButton#themeButton:!checked:hover {{
        background-color: #AAAAAA;
    }}

    QWidget:focus {{
        outline: none;
    }}

    /* Settings and About Scroll Content */
    QWidget#settingsScrollContent, QWidget#aboutScrollContent {{
         background-color: {bg1};
    }}
"""



# --- SVG Icon Data URIs (All icons are now rendered in white) ---
ICON_DATA_URIS = {
    "Home": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS1ob3VzZS1pY29uIGx1Y2lkZS1ob3VzZSI+PHBhdGggZD0iTTE1IDIxdi04YTEgMSAwIDAgMC0xLTFoLTRhMSAxIDAgMCAwLTEgMXY4Ii8+PHBhdGggZD0iTTMgMTBhMiAyIDAgMCAxIC43MDktMS41MjhsNy01Ljk5OWEyIDIgMCAwIDEgMi41ODIgMGw3IDUuOTk5QTIgMiAwIDAgMSAyMSAxMHY5YTIgMiAwIDAgMS0yIDJINWEyIDIgMCAwIDEtMi0yeiIvPjwvc3ZnPg==",

    "Settings": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS1zZXR0aW5ncy1pY29uIGx1Y2lkZS1zZXR0aW5ncyI+PHBhdGggZD0iTTEyLjIyIDJoLS40NGEyIDIgMCAwIDAtMiAydi4xOGEyIDIgMCAwIDEtMSAxLjczbC0uNDMuMjVhMiAyIDAgMCAxLTIgMGwtLjE1LS4wOGEyIDIgMCAwIDAtMi43My43M2wtLjIyLjM4YTIgMiAwIDAgMCAuNzMgMi43M2wuMTUuMWEyIDIgMCAwIDEgMSAxLjcydi41MWEyIDIgMCAwIDEtMSAxLjc0bC0uMTUuMDlhMiAyIDAgMCAwLS43MyAyLjczbC4yMi4zOGEyIDIgMCAwIDAgMi43My43M2wuMTUtLjA4YTIgMiAwIDAgMSAyIDBsLjQzLjI1YTIgMiAwIDAgMSAxIDEuNzNWMjBhMiAyIDAgMCAwIDIgMmguNDRhMiAyIDAgMCAwIDItMnYtLjE4YTIgMiAwIDAgMSAxLTEuNzNsLjQzLS4yNWEyIDIgMCAwIDEgMiAwbC4xNS4wOGEyIDIgMCAwIDAgMi43My0uNzNsLjIyLS4zOWEyIDIgMCAwIDAtLjczLTIuNzNsLS4xNS0uMDhhMiAyIDAgMCAxLTEtMS43NHYtLjVhMiAyIDAgMCAxIDEtMS43NGwuMTUtLjA5YTIgMiAwIDAgMCAuNzMtMi43M2wtLjIyLS4zOGEyIDIgMCAwIDAtMi43My0uNzNsLS4xNS4wOGEyIDIgMCAwIDEtMiAwbC0uNDMtLjI1YTIgMiAwIDAgMS0xLTEuNzNWNGEyIDIgMCAwIDAtMi0yeiIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjMiLz48L3N2Zz4=",

    "About": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS1jaXJjbGUtaGVscC1pY29uIGx1Y2lkZS1jaXJjbGUtaGVscCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48cGF0aCBkPSJNOS4wOSA5YTMgMyAwIDAgMSA1LjgzIDFjMCAyLTMgMy0zIDMiLz48cGF0aCBkPSJNMTIgMTdoLjAxIi8+PC9zdmc+",

    "Console": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS10ZXJtaW5hbC1pY29uIGx1Y2lkZS10ZXJtaW5hbCI+PHBvbHlsaW5lIHBvaW50cz0iNCAxNyAxMCAxMSA0IDUiLz48bGluZSB4MT0iMTIiIHgyPSIyMCIgeTE9IjE5IiB5Mj0iMTkiLz48L3N2Zz4=",

    "stop": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS1zcXVhcmUtaWNvbiBsdWNpZGUtc3F1YXJlIj48cmVjdCB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHg9IjMiIHk9IjMiIHJ4PSIyIi8+PC9zdmc+",

    "Download": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS1hcnJvdy1kb3duLXRvLWxpbmUtaWNvbiBsdWNpZGUtYXJyb3ctZG93bi10by1saW5lIj48cGF0aCBkPSJNMTIgMTdWMyIvPjxwYXRoIGQ9Im02IDExIDYgNiA2LTYiLz48cGF0aCBkPSJNMTkgMjFINSIvPjwvc3ZnPg==",

    "down_arrow": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS1tb3ZlLWRvd24taWNvbiBsdWNpZGUtbW92ZS1kb3duIj48cGF0aCBkPSJNOCAxOEwxMiAyMkwxNiAxOCIvPjxwYXRoIGQ9Ik0xMiAyVjIyIi8+PC9zdmc+"
}
