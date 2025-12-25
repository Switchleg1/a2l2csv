from ast import Constant
import lib.Constants as Constants
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLineEdit, QLabel, QCheckBox
from PyQt6.QtCore import QThread, QCoreApplication
from lib.LoadA2LThread import LoadA2LThread
from lib.SearchThread import SearchThread
from lib.SearchThread import SearchPosition
from lib.SearchThread import SearchType


class TABA2L(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.parent     = parent

        self.loadThread = LoadA2LThread()
        self.loadThread.logMessage.connect(self.parent.addLogEntry)
        self.loadThread.finished.connect(self.onFinishedLoading)

        self.searchThread = SearchThread()
        self.searchThread.addItem.connect(self._searchAddItem)
        self.searchThread.finished.connect(self._searchFinished)
        self.searchThread.search_position   = SearchPosition.CONTAIN

        self.tableItem      = ""
        self.tableRow       = 0
        self.searchItem     = None
        self.searchFound    = False
        self.overWritting   = False

        #Main layout box
        self.mainLayoutBox = QVBoxLayout()
        
        #Filename layout box
        self.fileNameLayoutBox = QHBoxLayout()
        self.fileLabel = QLabel()
        self.fileLabel.setFixedHeight(30)
        self.fileLabel.setText("Filename")
        self.fileNameLayoutBox.addWidget(self.fileLabel)

        self.fileEditBox = QLineEdit()
        self.fileEditBox.setFixedHeight(30)
        self.fileNameLayoutBox.addWidget(self.fileEditBox)

        self.findPushButton = QPushButton("Find")
        self.findPushButton.setFixedHeight(30)
        self.findPushButton.pressed.connect(self.FindButtonClick)
        self.fileNameLayoutBox.addWidget(self.findPushButton)

        self.mainLayoutBox.addLayout(self.fileNameLayoutBox)

        #Overwrite checkbox
        self.overwriteCheckBox = QCheckBox("Overwrite existing PID addresses")
        self.overwriteCheckBox.setChecked(False)
        self.mainLayoutBox.addWidget(self.overwriteCheckBox)

        #Load button
        self.loadPushButton = QPushButton("Load")
        self.loadPushButton.setFixedHeight(50)
        self.loadPushButton.pressed.connect(self.LoadButtonClick)
        self.mainLayoutBox.addWidget(self.loadPushButton)

        self.setLayout(self.mainLayoutBox)

        self._checkOverwrite()


    def FindButtonClick(self):
        a2lFileName = QFileDialog.getOpenFileName(self, "Open A2L", "", "A2L (*.a2l *.a2ldb)",)
        self.fileEditBox.setText(a2lFileName[0])


    def LoadButtonClick(self):
        self.loadThread.filename = self.fileEditBox.text()
        self.loadThread.start()
        self.loadPushButton.setEnabled(False)


    def onFinishedLoading(self):
        #overwrite list pid addresses
        if self.overwriteCheckBox.isChecked():
            self._overwritePIDS()

        else:
            self._loadA2L()


    def _checkOverwrite(self):
        self.overwriteCheckBox.setEnabled(True if self.parent.a2lsession is not None else False)


    def _overwritePIDS(self):
        if self.overWritting == True:
            self.parent.addLogEntry(f"Overwrite in progress, unable to start overwrite task")
            return

        self.overWritting   = True
        self.tableRow      = -1

        self._startNextSearch()


    def _startNextSearch(self):
        self.searchFound    = False
        self.searchItem     = None

        #get the next address that is not a virtual address
        self.tableRow       += 1
        self.tableItem      = self.parent.getListItem(self.tableRow)
        while self.tableItem is not None and "Name" in self.tableItem and "Address" in self.tableItem and self.tableItem["Address"] in Constants.VIRTUAL_ADDRESSES:
            self.tableRow       += 1
            self.tableItem      = self.parent.getListItem(self.tableRow)

        if self.tableItem is not None and "Name" in self.tableItem and "Address" in self.tableItem:
            #start search in original database search for address in pid list
            self.searchThread.a2lsession        = self.parent.a2lsession
            self.searchThread.search_string     = self.tableItem["Address"]
            self.searchThread.search_type       = SearchType.ADDR
            self.searchThread.items_left        = 0
            self.searchThread.start()

        else:
            self.overWritting = False
            self._loadA2L()


    def _searchAddItem(self, item):
        if self.searchThread.search_type == SearchType.ADDR:                    #original database search for address
            self.searchItem = item

        else:                                                                   #new database search for name
            if item is None or item["Name"] != self.searchItem["Name"]:
                return

            self.searchThread.items_left    = 0
            self.searchItem                 = item
            self.searchFound                = True
            self.parent.addLogEntry(f"Replacing {item["Name"]} [{self.tableItem["Name"]}] with address {item["Address"]}")
            self.tableItem["Address"] = item["Address"]
            self.parent.updateListItem(self.tableItem, self.tableRow)


    def _searchFinished(self):
        if self.searchThread.search_type == SearchType.NAME:        #search for name within the new database has finished
            if self.searchItem is None or self.searchFound == False:
                self.parent.addLogEntry(f"Unable to find address {self.tableItem["Address"]} [{self.tableItem["Name"]}] in new database")

            self._startNextSearch()

        else:                                                       #search for address within the original database has finished
            #if we didn't find the address we continue to the next PID
            if self.searchItem is None:
                self.parent.addLogEntry(f"Unable to find {self.tableItem["Name"]} [{self.tableItem["Address"]}] in original database")
                self._startNextSearch()

            else:
                #start search in new database search matching the name found in the previous database
                self.searchThread.a2lsession        = self.loadThread.a2lsession
                self.searchThread.search_string     = self.searchItem["Name"]
                self.searchThread.search_type       = SearchType.NAME
                self.searchThread.items_left        = Constants.MAX_SEARCH_ITEMS
                self.searchThread.start()


    def _loadA2L(self):
        #set current a2l database
        self.parent.a2ldb       = self.loadThread.a2ldb
        self.parent.a2lsession  = self.loadThread.a2lsession

        #update layout
        self.loadPushButton.setEnabled(True)
        self._checkOverwrite()

        # Switch to Search tab if file loaded successfully
        if self.parent.a2lsession is not None:
            self.parent.tabs.setCurrentIndex(1)