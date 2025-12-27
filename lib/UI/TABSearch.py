import lib.Helpers as Helpers
import lib.Constants as Constants
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QRadioButton, QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QAbstractItemView, QButtonGroup, QCheckBox, QGridLayout
from lib.SearchThread import SearchThread
from lib.SearchThread import SearchPosition
from lib.SearchThread import SearchType


class TABSearch(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.parent         = parent

        #Search thread
        self.searchThread   = SearchThread()
        self.searchThread.addItemsBatch.connect(self.addItemsBatch)                     # Connect the new batch signal for better performance
        self.searchThread.logMessage.connect(self.parent.addLogEntry)
        self.searchThread.finished.connect(self.onFinishedSearch)
        
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

        #Radios
        self.radioLayoutBox = QGridLayout()
        self.startRadioButton = QRadioButton("Starts with")
        self.radioLayoutBox.addWidget(self.startRadioButton, 0, 0)

        self.containRadioButton = QRadioButton("Contains")
        self.containRadioButton.setChecked(True)
        self.radioLayoutBox.addWidget(self.containRadioButton, 0, 1)

        self.endRadioButton = QRadioButton("Ends with")
        self.radioLayoutBox.addWidget(self.endRadioButton, 0, 2)

        self.equalsRadioButton = QRadioButton("Equals")
        self.radioLayoutBox.addWidget(self.equalsRadioButton, 0, 3)

        self.nameRadioButton = QRadioButton("Name")
        self.nameRadioButton.setChecked(True)
        self.radioLayoutBox.addWidget(self.nameRadioButton, 1, 0)

        self.descriptionRadioButton = QRadioButton("Description")
        self.radioLayoutBox.addWidget(self.descriptionRadioButton, 1, 1)

        self.addressRadioButton = QRadioButton("Address")
        self.radioLayoutBox.addWidget(self.addressRadioButton, 1, 2)

        self.mainLayoutBox.addLayout(self.radioLayoutBox)

        self.positionGroup = QButtonGroup()
        self.positionGroup.addButton(self.startRadioButton)
        self.positionGroup.addButton(self.containRadioButton)
        self.positionGroup.addButton(self.endRadioButton)
        self.positionGroup.addButton(self.equalsRadioButton)

        self.typeGroup = QButtonGroup()
        self.typeGroup.addButton(self.nameRadioButton)
        self.typeGroup.addButton(self.descriptionRadioButton)
        self.typeGroup.addButton(self.addressRadioButton)

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

        #Overwrite checkbox
        self.overwriteCheckBox = QCheckBox("Overwrite existing PIDs")
        self.overwriteCheckBox.setChecked(False)
        self.mainLayoutBox.addWidget(self.overwriteCheckBox)

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

            elif self.endRadioButton.isChecked():
                self.searchThread.search_position   = SearchPosition.END

            else:
                self.searchThread.search_position   = SearchPosition.EQ

            #set search type
            if self.nameRadioButton.isChecked():
                self.searchThread.search_type   = SearchType.NAME

            elif self.descriptionRadioButton.isChecked():
                self.searchThread.search_type   = SearchType.DESC

            else:
                self.searchThread.search_type   = SearchType.ADDR

            self.searchThread.items_left    = Constants.MAX_SEARCH_ITEMS
            self.searchThread.search_string = self.inputEditBox.text()
            self.searchThread.a2lsession    = self.parent.a2lsession
            self.searchThread.start()


    def AddButtonClick(self):
        overwrite = self.overwriteCheckBox.isChecked()
        selected_rows = set()
        for item in self.itemsTable.selectedItems():
            selected_rows.add(item.row())

        for row in sorted(selected_rows):
            # Get cell values safely, handling None cells
            name_item       = self.itemsTable.item(row, 0)
            unit_item       = self.itemsTable.item(row, 1)
            equation_item   = self.itemsTable.item(row, 2)
            address_item    = self.itemsTable.item(row, 3)
            length_item     = self.itemsTable.item(row, 4)
            signed_item     = self.itemsTable.item(row, 5)
            min_item        = self.itemsTable.item(row, 6)
            max_item        = self.itemsTable.item(row, 7)
            desc_item       = self.itemsTable.item(row, 8)

            # Skip row if essential fields are missing
            if not all([name_item, address_item, length_item, signed_item, min_item, max_item]):
                self.parent.addLogEntry(f"Skipped row {row + 1}: missing required fields")
                continue

            item = {
                "Name"          : name_item.text(),
                "Unit"          : unit_item.text() if unit_item else "",
                "Equation"      : equation_item.text() if equation_item else "",
                "Format"        : "%01.0f",
                "Address"       : address_item.text(),
                "Length"        : length_item.text(),
                "Signed"        : signed_item.text(),
                "ProgMin"       : min_item.text(),
                "ProgMax"       : max_item.text(),
                "WarnMin"       : Helpers.float_to_str(float(min_item.text()) - 1),
                "WarnMax"       : Helpers.float_to_str(float(max_item.text()) + 1),
                "Smoothing"     : "0",
                "Enabled"       : "TRUE",
                "Tabs"          : "",
                "Assign To"     : "",
                "Description"   : desc_item.text() if desc_item else ""
            }
            self.parent.addListItem(item, overwrite)

        self.parent.addLogEntry(f"Added {len(selected_rows)} items to list")


    def onFinishedSearch(self):
        self.searchPushButton.setText("Start")


    def addItemEntry(self, item):
        #self.parent.addLogEntry(f"Item: {item}")
        self.itemsTable.setRowCount(self.itemsTable.rowCount() + 1)

        for index, (key, value) in enumerate(item.items()):
            entryItem = QTableWidgetItem(value)
            self.itemsTable.setItem(self.itemsTable.rowCount() - 1, index, entryItem)


    def addItemsBatch(self, items):
        """Add multiple items to the table at once for better performance"""
        if not items:
            return
        
        # Disable sorting during batch insert for better performance
        self.itemsTable.setSortingEnabled(False)
        
        # Get current row count and set new row count all at once
        current_rows = self.itemsTable.rowCount()
        new_row_count = current_rows + len(items)
        self.itemsTable.setRowCount(new_row_count)
        
        # Add all items using the expected column order from Constants
        # This ensures columns match even if dict key order changes during signal emission
        for batch_index, item in enumerate(items):
            row = current_rows + batch_index
            for col_index, column_name in enumerate(Constants.SEARCH_DATA_COLUMNS):
                value = item.get(column_name, "")
                entryItem = QTableWidgetItem(value)
                self.itemsTable.setItem(row, col_index, entryItem)
        
        # Re-enable sorting after batch insert
        self.itemsTable.setSortingEnabled(True)
            