import lib.Helpers as Helpers
import lib.Constants as Constants
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QRadioButton, QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QAbstractItemView, QButtonGroup
from lib.SearchThread import SearchThread
from lib.SearchThread import SearchPosition
from lib.SearchThread import SearchType


class TABSearch(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.parent         = parent
        self.searchThread   = SearchThread(self.parent.addLogEntry, self.addItemEntry, self.onFinishedSearch)

        #Main layout box
        self.mainLayoutBox = QVBoxLayout()

        #Search layout box
        self.searchLayoutBox = QHBoxLayout()
        self.searchLabel = QLabel("Search")
        self.searchLabel.setFixedHeight(30)
        self.searchLayoutBox.addWidget(self.searchLabel)

        self.inputEditBox = QLineEdit()
        self.inputEditBox.setFixedHeight(30)
        self.inputEditBox.returnPressed.connect(self.SearchButtonClick)
        self.searchLayoutBox.addWidget(self.inputEditBox)
        
        self.mainLayoutBox.addLayout(self.searchLayoutBox)

        #Position radio
        self.positionLayoutBox = QHBoxLayout()
        self.startRadioButton = QRadioButton("Starts with")
        self.positionLayoutBox.addWidget(self.startRadioButton)

        self.containRadioButton = QRadioButton("Contains")
        self.containRadioButton.setChecked(True)
        self.positionLayoutBox.addWidget(self.containRadioButton)

        self.endRadioButton = QRadioButton("Ends with")
        self.positionLayoutBox.addWidget(self.endRadioButton)

        self.typeGroup = QButtonGroup()
        self.typeGroup.addButton(self.startRadioButton)
        self.typeGroup.addButton(self.containRadioButton)
        self.typeGroup.addButton(self.endRadioButton)

        self.mainLayoutBox.addLayout(self.positionLayoutBox)

        #Type radio
        self.typeLayoutBox = QHBoxLayout()
        self.nameRadioButton = QRadioButton("Name")
        self.nameRadioButton.setChecked(True)
        self.typeLayoutBox.addWidget(self.nameRadioButton)

        self.descriptionRadioButton = QRadioButton("Description")
        self.typeLayoutBox.addWidget(self.descriptionRadioButton)

        self.addressRadioButton = QRadioButton("Address")
        self.typeLayoutBox.addWidget(self.addressRadioButton)

        self.typeGroup = QButtonGroup()
        self.typeGroup.addButton(self.nameRadioButton)
        self.typeGroup.addButton(self.descriptionRadioButton)
        self.typeGroup.addButton(self.addressRadioButton)

        self.mainLayoutBox.addLayout(self.typeLayoutBox)

        #Search button
        self.searchPushButton = QPushButton("Search")
        self.searchPushButton.setFixedHeight(50)
        self.searchPushButton.pressed.connect(self.SearchButtonClick)
        self.mainLayoutBox.addWidget(self.searchPushButton)

        #Items table
        self.itemsTable = QTableWidget()
        self.itemsTable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.itemsTable.setColumnCount(len(Constants.SEARCH_DATA_COLUMNS))
        self.itemsTable.setHorizontalHeaderLabels(Constants.SEARCH_DATA_COLUMNS)
        for i in range(len(Constants.SEARCH_COLUMN_SIZES)):
            self.itemsTable.setColumnWidth(i, Constants.SEARCH_COLUMN_SIZES[i])

        self.mainLayoutBox.addWidget(self.itemsTable)

        #Add button
        self.addPushButton = QPushButton("Add to list")
        self.addPushButton.setFixedHeight(50)
        self.addPushButton.pressed.connect(self.AddButtonClick)
        self.mainLayoutBox.addWidget(self.addPushButton)

        self.setLayout(self.mainLayoutBox)


    def SearchButtonClick(self):
        if self.searchThread.isRunning():
            self.searchThread.terminate()
            self.parent.addLogEntry("Cancelled")
            self.searchPushButton.setText("Start")

        else:
            self.itemsTable.setRowCount(0)
            self.searchPushButton.setText("Cancel")

            #set search position
            if self.startRadioButton.isChecked():
                self.searchThread.search_position   = SearchPosition.START

            elif self.containRadioButton.isChecked():
                self.searchThread.search_position   = SearchPosition.CONTAIN

            else:
                self.searchThread.search_position   = SearchPosition.END

            #set search type
            if self.nameRadioButton.isChecked():
                self.searchThread.search_type   = SearchType.NAME

            elif self.descriptionRadioButton.isChecked():
                self.searchThread.search_type   = SearchType.DESC

            else:
                self.searchThread.search_type   = SearchType.ADDR

            self.searchThread.search_string = self.inputEditBox.text()
            self.searchThread.a2lsession    = self.parent.a2lsession
            self.searchThread.start()


    def AddButtonClick(self):
        for i in range(0, len(self.itemsTable.selectedItems()), len(Constants.SEARCH_DATA_COLUMNS)):
            item = {
                "Name"          : self.itemsTable.selectedItems()[i].text(),
                "Unit"          : self.itemsTable.selectedItems()[i + 1].text(),
                "Equation"      : self.itemsTable.selectedItems()[i + 2].text(),
                "Format"        : "%01.0f", 
                "Address"       : self.itemsTable.selectedItems()[i + 3].text(),
                "Length"        : self.itemsTable.selectedItems()[i + 4].text(),
                "Signed"        : self.itemsTable.selectedItems()[i + 5].text(),
                "ProgMin"       : self.itemsTable.selectedItems()[i + 6].text(),
                "ProgMax"       : self.itemsTable.selectedItems()[i + 7].text(),
                "WarnMin"       : Helpers.float_to_str(float(self.itemsTable.selectedItems()[i + 6].text()) - 1),
                "WarnMax"       : Helpers.float_to_str(float(self.itemsTable.selectedItems()[i + 7].text()) + 1),
                "Smoothing"     : "0",
                "Enabled"       : "TRUE",
                "Tabs"          : "",
                "Assign To"     : "",
                "Description"   : self.itemsTable.selectedItems()[i + 8].text()
            }
            self.parent.addListItem(item)

        self.parent.addLogEntry(f"Added {int(len(self.itemsTable.selectedItems()) / len(Constants.SEARCH_DATA_COLUMNS))} items to list")


    def onFinishedSearch(self):
        self.searchPushButton.setText("Start")


    def addItemEntry(self, item):
        #self.parent.addLogEntry(f"Item: {item}")
        self.itemsTable.setRowCount(self.itemsTable.rowCount() + 1)

        for index, (key, value) in enumerate(item.items()):
            entryItem = QTableWidgetItem(value)
            self.itemsTable.setItem(self.itemsTable.rowCount() - 1, index, entryItem)
            