import csv
import lib.Constants as Constants
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QAbstractItemView, QCheckBox


class TABList(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.parent         = parent

        #Main layout box
        self.mainLayoutBox = QVBoxLayout()

        #Buttons layout box
        self.buttonsLayoutBox = QHBoxLayout()

        self.importPushButton = QPushButton("Import")
        self.importPushButton.setFixedHeight(50)
        self.importPushButton.pressed.connect(self.ImportButtonClick)
        self.buttonsLayoutBox.addWidget(self.importPushButton)

        self.exportPushButton = QPushButton("Export")
        self.exportPushButton.setFixedHeight(50)
        self.exportPushButton.pressed.connect(self.ExportButtonClick)
        self.buttonsLayoutBox.addWidget(self.exportPushButton)

        self.mainLayoutBox.addLayout(self.buttonsLayoutBox)

        #Overwrite checkbox
        self.overwriteCheckBox = QCheckBox("Overwrite existing PIDs")
        self.overwriteCheckBox.setChecked(False)
        self.mainLayoutBox.addWidget(self.overwriteCheckBox)

        #Items table
        self.itemsTable = QTableWidget()
        self.itemsTable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.itemsTable.setColumnCount(len(Constants.LIST_DATA_COLUMNS))
        self.itemsTable.setHorizontalHeaderLabels(Constants.LIST_DATA_COLUMNS)
        for i in range(len(Constants.LIST_COLUMN_SIZES)):
            self.itemsTable.setColumnWidth(i, Constants.LIST_COLUMN_SIZES[i])

        self.mainLayoutBox.addWidget(self.itemsTable)

        #Remove button
        self.removePushButton = QPushButton("Remove")
        self.removePushButton.setFixedHeight(50)
        self.removePushButton.pressed.connect(self.RemoveButtonClick)
        self.mainLayoutBox.addWidget(self.removePushButton)

        self.setLayout(self.mainLayoutBox)


    def addListItem(self, item, overwrite=False):
        #ensure all required columns are present in item
        for column in Constants.LIST_DATA_COLUMNS_REQUIRED:
            if column not in item:
                self.parent.addLogEntry(f"Failed to add item to list: {item}")
                return

        # Check if item with same Address already exists
        existing_rows = []
        if overwrite:
            item_address = item.get("Address", "")
            address_col = Constants.LIST_DATA_COLUMNS.index("Address")
            for row in range(self.itemsTable.rowCount()):
                cell = self.itemsTable.item(row, address_col)
                if cell is not None and cell.text() == item_address:
                    existing_rows.append(row)
        
        # If overwrite mode and item exists, update all matching rows; otherwise add new row
        if existing_rows:
            # Update all existing rows with matching Address
            for target_row in existing_rows:
                for column_index in range(self.itemsTable.columnCount()):
                    column_str = Constants.LIST_DATA_COLUMNS[column_index]
                    entryItem = QTableWidgetItem(item[column_str] if column_str in item else "")
                    self.itemsTable.setItem(target_row, column_index, entryItem)

        else:
            # Add new row
            self.itemsTable.setRowCount(self.itemsTable.rowCount() + 1)
            target_row = self.itemsTable.rowCount() - 1
            for column_index in range(self.itemsTable.columnCount()):
                column_str = Constants.LIST_DATA_COLUMNS[column_index]
                entryItem = QTableWidgetItem(item[column_str] if column_str in item else "")
                self.itemsTable.setItem(target_row, column_index, entryItem)


    def getListItem(self, row):
        if row in range(self.itemsTable.rowCount()):
            item = {}
            for column_index in range(self.itemsTable.columnCount()):
                table_item = self.itemsTable.item(row, column_index)
                column_str = Constants.LIST_DATA_COLUMNS[column_index]
                item[column_str] = table_item.text() if table_item is not None else ""

            return item

        return None


    def updateListItem(self, item, row):
        if item is None:
            return

        if row in range(self.itemsTable.rowCount()):
            for column_index in range(self.itemsTable.columnCount()):
                column_str = Constants.LIST_DATA_COLUMNS[column_index]
                if column_str in item:
                    self.itemsTable.item(row, column_index).setText(item[column_str])


    def ImportButtonClick(self, csvFilename=None):
        overwrite = self.overwriteCheckBox.isChecked()
        
        # If no filename provided, show file dialog
        if csvFilename is None:
            csvFilename = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV (*.csv)",)
            if len(csvFilename[0]) == 0:
                return
        else:
            # If filename is a string, convert to tuple format expected by _loadCSV
            if isinstance(csvFilename, str):
                csvFilename = (csvFilename, "")
        
        self._loadCSV(overwrite, csvFilename)


    def _loadCSV(self, overwrite, csvFilename):
        try:
            with open(csvFilename[0], "r", newline='') as csvfile:
                csvreader = csv.DictReader(csvfile)

                for column_str in Constants.LIST_DATA_COLUMNS_REQUIRED:
                    if column_str not in csvreader.fieldnames:
                        self.parent.addLogEntry(f"Import failed: {csvFilename[0]} does not contain {column_str}")
                        return

                for row in csvreader:
                    self.addListItem(row, overwrite)

                self.checkForDuplicates()

                self.parent.addLogEntry(f"Import successful: {csvFilename[0]}")

        except Exception as e:
            self.parent.addLogEntry(f"Import failed: {csvFilename[0]} - {e}")


    def ExportButtonClick(self):
        csvFilename = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV (*.csv)",)
        if len(csvFilename[0]) == 0:
            return

        try:
            with open(csvFilename[0], "w", newline='') as csvfile:
                csvwriter = csv.DictWriter(csvfile, fieldnames=Constants.LIST_DATA_COLUMNS)

                data = []
                for row in range(self.itemsTable.rowCount(), 1):
                    dataEntry = {}
                    for column_index in range(self.itemsTable.columnCount()):
                        cell = self.itemsTable.item(row, column_index)
                        column_str = Constants.LIST_DATA_COLUMNS[column_index]
                        dataEntry[column_str] = cell.text() if cell is not None else ""

                    data.append(dataEntry)

                csvwriter.writeheader()
                csvwriter.writerows(data)
                self.parent.addLogEntry(f"Export successful: {csvFilename[0]}")

        except Exception as e:
            self.parent.addLogEntry(f"Export failed: {csvFilename[0]} - {e}")


    def RemoveButtonClick(self):
        while len(self.itemsTable.selectedItems()):
            self.itemsTable.removeRow(self.itemsTable.selectedItems()[0].row())

        self.checkForDuplicates()


    def checkForDuplicates(self):
        if Constants.CHECK_FOR_DUPLICATES == False:
            return

        try:
            #get address index
            address_index = Constants.LIST_DATA_COLUMNS.index("Address")

            #reset all rows to normal color
            for row in range(self.itemsTable.rowCount()):
                self._setRowColor(row, Constants.NORMAL_BACKGROUND_COLOR)

            for row in range(self.itemsTable.rowCount()):
                #if the row is already highlighted continue
                if self.itemsTable.item(row, 0).background() == Constants.DUPLICATE_BACKGROUND_COLOR:
                    continue

                #get address and see if its a virtual address, if so move on
                address = self.itemsTable.item(row, address_index).text().upper()
                if address in Constants.VIRTUAL_ADDRESSES:
                    self._setRowColor(row, Constants.NORMAL_BACKGROUND_COLOR)
                    continue

                #now compare address to all rows except its own
                isDuplicate = False
                for compareRow in range(row + 1, self.itemsTable.rowCount()):
                    compareAddress = self.itemsTable.item(compareRow, address_index).text().upper()
                    if compareAddress == address:
                        isDuplicate = True
                        self._setRowColor(compareRow, Constants.DUPLICATE_BACKGROUND_COLOR)

                #did we find a duplicate?
                if isDuplicate:
                    self._setRowColor(row, Constants.DUPLICATE_BACKGROUND_COLOR)

        except Exception as e:
            self.parent.addLogEntry(f"Check for duplicates failed: {e}")


    def _setRowColor(self, row, color):
        for column_index in range(self.itemsTable.columnCount()):
            self.itemsTable.item(row, column_index).setBackground(color)