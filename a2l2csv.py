import sys
import os
import argparse
import lib.Constants as Constants
from lib.Constants import DBType
from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QListWidget, QTabWidget, QProgressBar
from pya2l import DB
from lib.UI.TABDatabase import TABDatabase
from lib.UI.TABSearch import TABSearch
from lib.UI.TABList import TABList


class MainWindow(QMainWindow):
    def __init__(self, db_file=None, csv_file=None):
        super().__init__()

        #Variables used to hold database
        self.db_type        = DBType.NONE
        self.a2ldb          = DB()
        self.a2lsession     = None
        self.csv_name_db    = {}
        self.csv_desc_db    = {}
        self.csv_address_db = {}

        # Store CSV file to load after A2L is loaded
        self.pending_csv_file = csv_file 

        #set title
        self.setWindowTitle(Constants.APPLICATION_VERSION_STRING)

        #main layout
        mainLayoutBox = QVBoxLayout()

        #tabs
        self.listTab = TABList(self)
        self.dbTab = TABDatabase(self)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.dbTab, "Database")
        self.tabs.addTab(TABSearch(self), "Search")
        self.tabs.addTab(self.listTab, "List")

        mainLayoutBox.addWidget(self.tabs)

        #log box
        self.listViewLog = QListWidget()
        self.listViewLog.setFixedHeight(100)

        mainLayoutBox.addWidget(self.listViewLog)

        #progress bar
        self.progressBars = [QProgressBar(), QProgressBar()]
        for index in range(len(self.progressBars)):
            self.progressBars[index].setVisible(False)
            mainLayoutBox.addWidget(self.progressBars[index])

        widget = QWidget()
        widget.setLayout(mainLayoutBox)
        self.setGeometry(300, 300, 650, 600)
        self.setCentralWidget(widget)
        self.show()

        # If db_file was provided, load it automatically
        if db_file:
            self.dbTab.fileEditBox.setText(db_file)
            self.dbTab.LoadButtonClick()
        elif csv_file:
            # If only CSV provided without DB, load it immediately
            self.listTab.ImportButtonClick(csvFilename=csv_file)
            # Switch to List tab to show the imported data
            self.tabs.setCurrentIndex(2)


    def addLogEntry(self, entry):
        self.listViewLog.addItem(entry)
        self.listViewLog.scrollToBottom()


    def addListItem(self, item, overwrite=False):
        self.listTab.addListItem(item, overwrite)


    def getListItemCount(self):
        return self.listTab.getListItemCount()


    def getListItem(self, row):
        return self.listTab.getListItem(row)


    def updateListItem(self, item, row):
        self.listTab.updateListItem(item, row)


    def checkForDuplicates(self):
        self.listTab.checkForDuplicates()


    def updateProgress(self, index, current_value):
        self.progressBars[index].setValue(current_value)


    def setupProgress(self, index, min_value, max_value, isVisible):
        self.progressBars[index].setMinimum(min_value)
        self.progressBars[index].setMaximum(max_value)
        self.progressBars[index].setVisible(isVisible)


    def checkAndLoadPendingCSV(self):
        """Check if DB is loaded and load pending CSV if present"""
        if self.pending_csv_file and self.a2lsession:
            # Use TABList's ImportButtonClick method with the filename
            self.listTab.ImportButtonClick(csvFilename=self.pending_csv_file)
            # Switch to List tab to show the imported data
            self.tabs.setCurrentIndex(2)
            self.pending_csv_file = None  # Clear after loading



def print_usage():
    """Print usage information and exit."""
    print(f"""
Usage: python a2l2csv.py [DB_FILE] [OPTIONS]

A2L to CSV converter application.

Arguments:
  DB_FILE              Optional path to an .a2l, .a2ldb or .csv file to load automatically.
                        If provided, the application will skip the Load A2L tab and go
                        directly to the Search tab with the file loaded.

Options:
  -p, --pid-list FILE   Optional path to a .csv file containing PID list to import.
                        If provided with DB_FILE, the CSV will be loaded after the DB.
                        If provided alone, the CSV will be loaded immediately.
  -h, --help            Show this help message and exit.

Examples:
  python a2l2csv.py                              # Start with empty tabs
  python a2l2csv.py myfile.a2l                   # Load A2L file automatically
  python a2l2csv.py database.a2ldb               # Load A2L database automatically
  python a2l2csv.py database.csv                 # Load CSV database automatically
  python a2l2csv.py myfile.a2l -p pids.csv       # Load A2L then import PID list
  python a2l2csv.py --pid-list pids.csv          # Import PID list only

Supported file types:
  DB files: .a2l, .a2ldb or .csv
  CSV files: .csv (must contain required PID columns)
""")
    sys.exit(1)


def validate_db_file(filepath):
    """
    Validate that the provided file path is a valid .a2l, .a2ldb or .csv file.
    
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
        print(f"Error: Database file not found: {filepath}")
        print_usage()
    
    # Check file extension
    _, ext = os.path.splitext(filepath)
    if ext.lower() not in ['.a2l', '.a2ldb', '.csv']:
        print(f"Error: Invalid database file type '{ext}'. Expected .a2l, .a2ldb or .csv")
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
    parser.add_argument('db_file', nargs='?', help='Optional .a2l, .a2ldb or .csv file to load')
    parser.add_argument('-p', '--pid-list', dest='csv_file', help='Optional .csv file with PID list to import')
    parser.add_argument('-h', '--help', action='store_true', help='Show help message')
    
    args = parser.parse_args()
    
    # Show help if requested
    if args.help:
        print_usage()
    
    # Validate files if provided
    db_file = validate_db_file(args.db_file) if args.db_file else None
    csv_file = validate_csv_file(args.csv_file) if args.csv_file else None
    
    # Start application
    app = QApplication(sys.argv)
    w = MainWindow(db_file=db_file, csv_file=csv_file)
    app.exec()