import sys
import os
import argparse
import lib.Constants as Constants
from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QListWidget, QTabWidget
from pya2l import DB
from lib.UI.TABA2L import TABA2L
from lib.UI.TABSearch import TABSearch
from lib.UI.TABList import TABList


class MainWindow(QMainWindow):
    def __init__(self, a2l_file=None, csv_file=None):
        super().__init__()

        #Variables used to hold a2l database
        self.a2ldb      = DB()
        self.a2lsession = None
        self.pending_csv_file = csv_file  # Store CSV file to load after A2L is loaded

        #set title
        self.setWindowTitle(Constants.APPLICATION_VERSION_STRING)

        #tabs
        self.listTab = TABList(self)
        self.a2lTab = TABA2L(self)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.a2lTab, "A2L")
        self.tabs.addTab(TABSearch(self), "Search")
        self.tabs.addTab(self.listTab, "List")

        #log box
        self.listViewLog = QListWidget()
        self.listViewLog.setFixedHeight(100)
        layoutLog = QVBoxLayout()
        layoutLog.addWidget(self.listViewLog)

        layoutBoxAll = QVBoxLayout()
        layoutBoxAll.addWidget(self.tabs)
        layoutBoxAll.addLayout(layoutLog)

        widget = QWidget()
        widget.setLayout(layoutBoxAll)
        self.setGeometry(300, 300, 650, 600)
        self.setCentralWidget(widget)
        self.show()

        # If a2l_file was provided, load it automatically
        if a2l_file:
            self.a2lTab.fileEditBox.setText(a2l_file)
            self.a2lTab.LoadButtonClick()
        elif csv_file:
            # If only CSV provided without A2L, load it immediately
            self.listTab.ImportButtonClick(csvFilename=csv_file)
            # Switch to List tab to show the imported data
            self.tabs.setCurrentIndex(2)


    def addLogEntry(self, entry):
        self.listViewLog.addItem(entry)
        self.listViewLog.scrollToBottom()


    def addListItem(self, item, overwrite=False):
        self.listTab.addListItem(item, overwrite)


    def getListItem(self, row):
        return self.listTab.getListItem(row)


    def updateListItem(self, item, row):
        self.listTab.updateListItem(item, row)


    def checkAndLoadPendingCSV(self):
        """Check if A2L is loaded and load pending CSV if present"""
        if self.pending_csv_file and self.a2lsession:
            # Use TABList's ImportButtonClick method with the filename
            self.listTab.ImportButtonClick(csvFilename=self.pending_csv_file)
            # Switch to List tab to show the imported data
            self.tabs.setCurrentIndex(2)
            self.pending_csv_file = None  # Clear after loading


def print_usage():
    """Print usage information and exit."""
    print(f"""
Usage: python a2l2csv.py [A2L_FILE] [OPTIONS]

A2L to CSV converter application.

Arguments:
  A2L_FILE              Optional path to an .a2l or .a2ldb file to load automatically.
                        If provided, the application will skip the Load A2L tab and go
                        directly to the Search tab with the file loaded.

Options:
  -p, --pid-list FILE   Optional path to a .csv file containing PID list to import.
                        If provided with A2L_FILE, the CSV will be loaded after the A2L.
                        If provided alone, the CSV will be loaded immediately.
  -h, --help            Show this help message and exit.

Examples:
  python a2l2csv.py                              # Start with empty tabs
  python a2l2csv.py myfile.a2l                   # Load A2L file automatically
  python a2l2csv.py database.a2ldb               # Load A2L database automatically
  python a2l2csv.py myfile.a2l -p pids.csv       # Load A2L then import PID list
  python a2l2csv.py --pid-list pids.csv          # Import PID list only

Supported file types:
  A2L files: .a2l, .a2ldb
  CSV files: .csv (must contain required PID columns)
""")
    sys.exit(1)


def validate_a2l_file(filepath):
    """
    Validate that the provided file path is a valid .a2l or .a2ldb file.
    
    Args:
        filepath: Path to the file to validate
        
    Returns:
        str: Absolute path to the file if valid, None if empty string
        
    Exits:
        Prints usage and exits if file is invalid
    """
    if not filepath or filepath == "":
        return None
    
    # Check if file exists
    if not os.path.isfile(filepath):
        print(f"Error: A2L file not found: {filepath}")
        print_usage()
    
    # Check file extension
    _, ext = os.path.splitext(filepath)
    if ext.lower() not in ['.a2l', '.a2ldb']:
        print(f"Error: Invalid A2L file type '{ext}'. Expected .a2l or .a2ldb")
        print_usage()
    
    return os.path.abspath(filepath)


def validate_csv_file(filepath):
    """
    Validate that the provided file path is a valid .csv file.
    
    Args:
        filepath: Path to the file to validate
        
    Returns:
        str: Absolute path to the file if valid, None if empty string
        
    Exits:
        Prints usage and exits if file is invalid
    """
    if not filepath or filepath == "":
        return None
    
    # Check if file exists
    if not os.path.isfile(filepath):
        print(f"Error: CSV file not found: {filepath}")
        print_usage()
    
    # Check file extension
    _, ext = os.path.splitext(filepath)
    if ext.lower() != '.csv':
        print(f"Error: Invalid CSV file type '{ext}'. Expected .csv")
        print_usage()
    
    return os.path.abspath(filepath)


# Main
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(add_help=False)  # Disable default help to use custom
    parser.add_argument('a2l_file', nargs='?', help='Optional .a2l or .a2ldb file to load')
    parser.add_argument('-p', '--pid-list', dest='csv_file', help='Optional .csv file with PID list to import')
    parser.add_argument('-h', '--help', action='store_true', help='Show help message')
    
    args = parser.parse_args()
    
    # Show help if requested
    if args.help:
        print_usage()
    
    # Validate files if provided
    a2l_file = validate_a2l_file(args.a2l_file) if args.a2l_file else None
    csv_file = validate_csv_file(args.csv_file) if args.csv_file else None
    
    # Start application
    app = QApplication(sys.argv)
    w = MainWindow(a2l_file=a2l_file, csv_file=csv_file)
    app.exec()