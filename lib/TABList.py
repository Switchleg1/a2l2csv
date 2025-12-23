import lib.Constants as Constants
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QRadioButton, QFileDialog, QLineEdit, QLabel, QFrame, QTableWidget, QTableWidgetItem, QAbstractItemView


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
        #self.parent.addLogEntry(f"Item: {item}")
        self.itemsTable.setRowCount(self.itemsTable.rowCount() + 1)

        for index, (key, value) in enumerate(item.items()):
            entryItem = QTableWidgetItem(value)
            self.itemsTable.setItem(self.itemsTable.rowCount() - 1, index, entryItem)


    def ImportButtonClick(self):
        a2lFileName = QFileDialog.getOpenFileName(self, "Open A2L", "", "A2L (*.a2l;*.a2ldb)",)
        self.parent.addLogEntry("Import")


    def ExportButtonClick(self):
        a2lFileName = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV (*.csv)",)
        self.parent.addLogEntry("Export")


    def RemoveButtonClick(self):
        while len(self.itemsTable.selectedItems()):
            #self.parent.addLogEntry(f"Remove row {self.itemsTable.selectedItems()[0].row()}")
            self.itemsTable.removeRow(self.itemsTable.selectedItems()[0].row())
            