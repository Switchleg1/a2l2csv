import time
import csv
import lib.Constants as Constants
import lib.Helpers as Helpers
from lib.SearchThread import SearchThread
from lib.Constants import SearchPosition
from lib.Constants import SearchType
from lib.Constants import DBType


class ExportThread():
    def __init__(self, logMessage, updateProgress, setupProgress, finished):
        super().__init__()

        self.logMessage         = logMessage
        self.updateProgress     = updateProgress
        self.setupProgress      = setupProgress
        self.finished           = finished

        self.searchThread = SearchThread()
        self.searchThread.addItem.connect(self._searchAddItem)
        self.searchThread.updateProgress.connect(self.updateProgress)
        self.searchThread.setupProgress.connect(self.setupProgress)
        self.searchThread.finished.connect(self._searchFinished)

        self.filename               = ""
        self.isRunning              = False
        self.startTime              = 0
        self.exportItems            = []
     
        self.dbType                 = DBType.NONE
        self.a2lSession             = None
        self.csvNameDB              = {}
        self.csvAddressDB           = {}


    def start(self):
        if self.isRunning == True:
            self.logMessage(f"Export in progress, unable to start export task")
            self.finished()
            return

        self.logMessage(f"Exporting database to file: {self.filename}")

        self.isRunning                      = True
        self.startTime                      = time.time()
        self.exportItems                    = []

        self.searchThread.db_type           = self.dbType
        self.searchThread.a2lsession        = self.a2lSession
        self.searchThread.csv_name_db       = self.csvNameDB
        self.searchThread.search_position   = SearchPosition.CONTAIN
        self.searchThread.search_string     = ""
        self.searchThread.items_left        = Constants.MAX_SEARCH_ITEMS
        self.searchThread.start()


    def _searchAddItem(self, item):
        export_item = {
            "Name"          : item["Name"],
            "Unit"          : item["Unit"],
            "Equation"      : item["Equation"],
            "Format"        : item["Format"],
            "Address"       : item["Address"],
            "Length"        : item["Length"],
            "Signed"        : item["Signed"],
            "ProgMin"       : item["Min"],
            "ProgMax"       : item["Max"],
            "WarnMin"       : Helpers.float_to_str(float(item["Min"]) - 1),
            "WarnMax"       : Helpers.float_to_str(float(item["Max"]) + 1),
            "Smoothing"     : "0",
            "Enabled"       : "TRUE",
            "Tabs"          : "",
            "Assign To"     : "",
            "Description"   : item["Description"]
        }
        self.exportItems.append(export_item)


    def _searchFinished(self):
        try:
            with open(self.filename, "w", encoding="latin-1", newline='') as csvfile:
                csvwriter = csv.DictWriter(csvfile, fieldnames=Constants.LIST_DATA_COLUMNS)

                csvwriter.writeheader()
                csvwriter.writerows(self.exportItems)

                elapsed_time = time.time() - self.startTime
                self.logMessage(f"Finished after {elapsed_time:.2f} seconds")

        except Exception as e:
            self.logMessage(f"Failed after {elapsed_time:.2f} seconds - {e}")
            
        self.isRunning = False
        self.finished()