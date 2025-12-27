from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTableWidgetItem


#list of constants for application

APPLICATION_VERSION_MAJOR       = 0
APPLICATION_VERSION_MINOR       = 2
APPLICATION_VERSION_STRING      = f"A2L2CSV v{APPLICATION_VERSION_MAJOR}.{APPLICATION_VERSION_MINOR}"
SEARCH_DATA_COLUMNS             = ["Name", "Unit", "Equation", "Address", "Length", "Signed", "Min", "Max", "Description"]
SEARCH_COLUMN_SIZES             = [175, 50, 200, 85, 45, 50, 50, 50, 750]
LIST_DATA_COLUMNS_REQUIRED      = ["Name", "Unit", "Equation", "Format", "Address", "Length", "Signed", "ProgMin", "ProgMax", "WarnMin", "WarnMax", "Smoothing", "Enabled", "Tabs", "Assign To"]
LIST_DATA_COLUMNS               = LIST_DATA_COLUMNS_REQUIRED + ["Description"]
LIST_COLUMN_SIZES               = [175, 50, 200, 75, 85, 50, 50, 65, 65, 65, 65, 65, 50, 150, 150, 750]
VIRTUAL_ADDRESSES               = ["0XFF", "0XFFFF", "0XFFFFFFFF"]
NORMAL_BACKGROUND_COLOR         = QTableWidgetItem().background()
DUPLICATE_BACKGROUND_COLOR      = QColor(120, 24, 24)
MAX_SEARCH_ITEMS                = 20000
SEARCH_BATCH_SIZE               = 100
APPLY_SQL_OPTIMIZATIONS         = False

DATA_LENGTH = {
    "UWORD": "2",
    "UBYTE": "1",
    "SBYTE": "1",
    "SWORD": "2",
    "ULONG": "4",
    "SLONG": "4",
    "FLOAT32_IEEE": "4",
}

DATA_SIGNED = {
    "UWORD": "FALSE",
    "UBYTE": "FALSE",
    "SBYTE": "TRUE",
    "SWORD": "TRUE",
    "ULONG": "FALSE",
    "SLONG": "TRUE",
    "FLOAT32_IEEE": "FALSE",
}