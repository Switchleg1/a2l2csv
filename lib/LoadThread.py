import csv
import time
import lib.Constants as Constants
from PyQt6.QtCore import QThread, pyqtSignal
from pya2l import DB
from lib.Constants import DBType


class LoadThread(QThread):
    logMessage      = pyqtSignal(str)
    updateProgress  = pyqtSignal(int, int)
    setupProgress   = pyqtSignal(int, int, int, bool)

    def __init__(self):
        super().__init__()

        self.db_type        = DBType.NONE
        self.a2ldb          = None
        self.a2lsession     = None
        self.csv_name_db    = {}
        self.csv_desc_db    = {}
        self.csv_address_db = {}
        self.filename       = ""
        self.start_time     = 0


    def run(self):
        self.logMessage.emit(f"Loading database file: {self.filename}")

        self.a2ldb          = None
        self.a2lsession     = None
        self.csv_name_db    = {}
        self.csv_desc_db    = {}
        self.csv_address_db = {}
        self.start_time     = time.time()

        try:
            file_extension = self.filename.split(".")[-1]

            if file_extension.lower() == "csv":
                self._loadCSV()

            else:
                self._loadA2L()

        except Exception as e:
            self.logMessage.emit(f"Failed after {self._elapsedTime():.2f} seconds - {e}")


    def _loadA2L(self):
        self.a2ldb = DB()

        try:
            self.a2lsession = (
                self.a2ldb.open_existing(self.filename)
            )
            
            # Apply SQLite performance optimizations
            # These pragmas improve query performance on all platforms (Windows, macOS, Linux)
            if Constants.APPLY_SQL_OPTIMIZATIONS:
                try:
                    self.a2lsession.execute("PRAGMA journal_mode=WAL")
                    self.a2lsession.execute("PRAGMA synchronous=NORMAL")
                    self.a2lsession.execute("PRAGMA cache_size=-64000")  # 64MB cache
                    self.a2lsession.execute("PRAGMA temp_store=MEMORY")
                    self.a2lsession.commit()
                except Exception as e:
                    # If pragmas fail, log but continue - database will still work
                    self.logMessage.emit(f"Note: Could not apply SQLite optimizations: {e}")

        except:
            self.logMessage.emit(f"Wait for database to build")

            self.a2lsession = (
                self.a2ldb.import_a2l(self.filename, encoding="latin-1")
            )

        self.db_type = DBType.A2L
        self.logMessage.emit(f"Finished after {self._elapsedTime():.2f} seconds")


    def _loadCSV(self):
        with open(self.filename, "r", encoding="latin-1", newline='') as csvfile:
            #get row count from csv file
            csvreader = csv.DictReader(csvfile)
            row_count = sum(1 for row in csvreader)

            #rewind and load csv data
            csvfile.seek(0)
            csvreader = csv.DictReader(csvfile)

            for column_str in Constants.LIST_DATA_COLUMNS_REQUIRED:
                if column_str not in csvreader.fieldnames:
                    self.logMessage.emit(f"Failed to load: does not contain {column_str}")
                    return

            #show progress bar
            self.updateProgress.emit(0, 0)
            self.setupProgress.emit(0, 0, row_count, True)

            item_count = 0
            for row in csvreader:
                self.csv_name_db[row["Name"]] = {
                    "Name"          : row["Name"],
                    "Unit"          : row["Unit"],
                    "Equation"      : row["Equation"],
                    "Format"        : row["Format"],
                    "Address"       : row["Address"],
                    "Length"        : row["Length"],
                    "Signed"        : row["Signed"],
                    "ProgMin"       : row["ProgMin"],
                    "ProgMax"       : row["ProgMax"],
                    "WarnMin"       : row["WarnMin"],
                    "WarnMax"       : row["WarnMax"],
                    "Smoothing"     : row["Smoothing"],
                    "Enabled"       : row["Enabled"],
                    "Tabs"          : row["Tabs"],
                    "Assign To"     : row["Assign To"],
                    "Description"   : row["Description"] if "Description" in row else "",
                }

                if "Description" in row:
                    self.csv_desc_db[row["Description"]] = {
                        "Name"          : row["Name"],
                        "Unit"          : row["Unit"],
                        "Equation"      : row["Equation"],
                        "Format"        : row["Format"],
                        "Address"       : row["Address"],
                        "Length"        : row["Length"],
                        "Signed"        : row["Signed"],
                        "ProgMin"       : row["ProgMin"],
                        "ProgMax"       : row["ProgMax"],
                        "WarnMin"       : row["WarnMin"],
                        "WarnMax"       : row["WarnMax"],
                        "Smoothing"     : row["Smoothing"],
                        "Enabled"       : row["Enabled"],
                        "Tabs"          : row["Tabs"],
                        "Assign To"     : row["Assign To"],
                        "Description"   : row["Description"] if "Description" in row else "",
                    }

                self.csv_address_db[row["Address"]] = {
                    "Name"          : row["Name"],
                    "Unit"          : row["Unit"],
                    "Equation"      : row["Equation"],
                    "Format"        : row["Format"],
                    "Address"       : row["Address"],
                    "Length"        : row["Length"],
                    "Signed"        : row["Signed"],
                    "ProgMin"       : row["ProgMin"],
                    "ProgMax"       : row["ProgMax"],
                    "WarnMin"       : row["WarnMin"],
                    "WarnMax"       : row["WarnMax"],
                    "Smoothing"     : row["Smoothing"],
                    "Enabled"       : row["Enabled"],
                    "Tabs"          : row["Tabs"],
                    "Assign To"     : row["Assign To"],
                    "Description"   : row["Description"] if "Description" in row else "",
                }

                #update progress bar
                item_count += 1
                if item_count % Constants.SEARCH_BATCH_SIZE == 0:
                    self.updateProgress.emit(0, item_count)

            self.db_type = DBType.CSV
            self.logMessage.emit(f"Finished loading {item_count} items after {self._elapsedTime():.2f} seconds")

            #hide progress bar
            self.setupProgress.emit(0, 0, 0, False)


    def _elapsedTime(self):
        return time.time() - self.start_time