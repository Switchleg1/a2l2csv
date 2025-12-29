import time
import lib.Constants as Constants
from lib.SearchThread import SearchThread
from lib.Constants import SearchPosition
from lib.Constants import SearchType
from lib.Constants import DBType


class ReplaceThread():
    def __init__(self, logMessage, getListItemCount, getListItem, updateListItem, updateProgress, setupProgress, finished):
        super().__init__()

        self.logMessage         = logMessage
        self.getListItemCount   = getListItemCount
        self.getListItem        = getListItem
        self.updateListItem     = updateListItem
        self.updateProgress     = updateProgress
        self.setupProgress      = setupProgress
        self.finished           = finished

        self.searchThread = SearchThread()
        self.searchThread.addItem.connect(self._searchAddItem)
        self.searchThread.finished.connect(self._searchFinished)
        self.searchThread.search_position = SearchPosition.EQ

        self.isRunning              = False
        self.searchStartTime        = 0
        self.replaceItemCount       = 0
        self.searchItemCount        = 0

        self.tableItem              = None
        self.tableRow               = 0
        self.searchItem             = None
        self.searchFound            = False

        self.newDBType              = DBType.NONE
        self.newA2LSession          = None
        self.newCSVNameDB           = {}
        self.newCSVAddressDB        = {}

        self.originalDBType         = DBType.NONE
        self.originalA2LSession     = None
        self.originalCSVNameDB      = {}
        self.originalCSVAddressDB   = {}


    def start(self):
        if self.isRunning == True:
            self.logMessage(f"Overwrite in progress, unable to start overwrite task")
            return

        self.isRunning              = True
        self.searchStartTime        = time.time()
        self.replaceItemCount       = 0
        self.searchItemCount        = 0

        self.tableItem              = None
        self.tableRow               = -1
        self.searchItem             = None
        self.searchFound            = False

        self.updateProgress(0, 0)
        self.setupProgress(0, 0, self.getListItemCount(), True)

        self._startNextSearch()


    def _startNextSearch(self):
        self.searchFound        = False
        self.searchItem         = None

        self.tableRow += 1
        self.updateProgress(0, self.tableRow)

        self.tableItem = self.getListItem(self.tableRow)

        #skip virtual addresses
        while self.tableItem is not None and "Name" in self.tableItem and "Address" in self.tableItem and self.tableItem["Address"].upper() in Constants.VIRTUAL_ADDRESSES:
            self.tableRow += 1
            self.tableItem = self.getListItem(self.tableRow)

        #finish when getListItem returns None
        if self.tableItem is None or not "Name" in self.tableItem or not "Address" in self.tableItem:
            elapsed_time = time.time() - self.searchStartTime
            self.logMessage(f"Replaced {self.replaceItemCount} out of {self.searchItemCount} items in {elapsed_time:.2f} seconds")

            self.isRunning = False
            self.setupProgress(0, 0, 0, False)
            self.finished()
            return

        #start search in original database search for address in pid list
        self.searchThread.db_type           = self.originalDBType
        self.searchThread.a2lsession        = self.originalA2LSession
        self.searchThread.csv_name_db       = self.originalCSVNameDB
        self.searchThread.csv_address_db    = self.originalCSVAddressDB
        self.searchThread.search_string     = self.tableItem["Address"]
        self.searchThread.search_type       = SearchType.ADDR
        self.searchThread.items_left        = 0
        self.searchThread.start()


    def _searchAddItem(self, item):
        if self.searchThread.search_type == SearchType.ADDR:                    #original database search for address
            self.searchItem = item

        else:                                                                   #new database search for name
            if item is None or item["Name"] != self.searchItem["Name"]:
                return

            self.searchThread.items_left    = 0
            self.searchItem                 = item
            self.searchFound                = True
            self.tableItem["Address"]       = item["Address"]
            #self.logMessage(f"Replacing {item["Name"]} [{self.tableItem["Name"]}] with address {self.tableItem["Address"]}")
            self.updateListItem(self.tableItem, self.tableRow)
            self.replaceItemCount += 1


    def _searchFinished(self):
        if self.searchThread.search_type == SearchType.NAME:        #search for name within the new database has finished
            if self.searchItem is None or self.searchFound == False:
                self.logMessage(f"Unable to find name {self.searchItem["Name"] if self.searchItem is not None else ""} [{self.tableItem["Name"]}] in new database")

            self.searchItemCount += 1
            self._startNextSearch()

        else:                                                       #search for address within the original database has finished
            #if we didn't find the address we continue to the next PID
            if self.searchItem is None:
                self.logMessage(f"Unable to find address {self.tableItem["Address"]} [{self.tableItem["Name"]}] in original database")
                self.searchItemCount += 1
                self._startNextSearch()

            else:
                #start search in new database search matching the name found in the previous database
                self.searchThread.db_type           = self.newDBType
                self.searchThread.a2lsession        = self.newA2LSession
                self.searchThread.csv_name_db       = self.newCSVNameDB
                self.searchThread.csv_address_db    = self.newCSVAddressDB
                self.searchThread.search_string     = self.searchItem["Name"]
                self.searchThread.search_type       = SearchType.NAME
                self.searchThread.items_left        = 0
                self.searchThread.start()