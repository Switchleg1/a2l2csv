import csv
import lib.Constants as Constants
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QAbstractItemView


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


    def addListItem(self, item):
        self.itemsTable.setRowCount(self.itemsTable.rowCount() + 1)

        for index, (key, value) in enumerate(item.items()):
            entryItem = QTableWidgetItem(value)
            self.itemsTable.setItem(self.itemsTable.rowCount() - 1, index, entryItem)


    def ImportButtonClick(self):
        csvFilename = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV (*.csv)",)
        if len(csvFilename[0]) == 0:
            return

        try:
            with open(csvFilename[0], "r", newline='') as csvfile:
                csvreader = csv.DictReader(csvfile)
                for column in Constants.LIST_DATA_COLUMNS_REQUIRED:
                    if column not in csvreader.fieldnames:
                        self.parent.addLogEntry(f"Import failed: {csvFilename[0]} does not contain {column}")
                        return

                for row in csvreader:
                    self.itemsTable.setRowCount(self.itemsTable.rowCount() + 1)

                    for index, (key, value) in enumerate(row.items()):
                        entryItem = QTableWidgetItem(value)
                        self.itemsTable.setItem(self.itemsTable.rowCount() - 1, index, entryItem)


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
                for row in range(0, self.itemsTable.rowCount(), 1):
                    dataEntry = {}
                    for i in range(0, self.itemsTable.columnCount(), 1):
                        dataEntry[Constants.LIST_DATA_COLUMNS[i]] = self.itemsTable.item(row, i).text()

                    data.append(dataEntry)

                csvwriter.writeheader()
                csvwriter.writerows(data)
                self.parent.addLogEntry(f"Export successful: {csvFilename[0]}")

        except Exception as e:
            self.parent.addLogEntry(f"Export failed: {csvFilename[0]} - {e}")


    def RemoveButtonClick(self):
        while len(self.itemsTable.selectedItems()):
            self.itemsTable.removeRow(self.itemsTable.selectedItems()[0].row())
            