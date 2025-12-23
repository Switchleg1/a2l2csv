import sys
import lib.Constants as Constants
from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QListWidget, QTabWidget
from pya2l import DB, model
from pya2l.api import inspect
from lib.TABA2L import TABA2L
from lib.TABSearch import TABSearch
from lib.TABList import TABList


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        #Variables used to hold a2l database
        self.a2ldb      = DB()
        self.a2lsession = None

        #set title
        self.setWindowTitle(Constants.APPLICATION_VERSION_STRING)

        #tabs
        self.listTab = TABList(self)

        self.tabs = QTabWidget()
        self.tabs.addTab(TABA2L(self), "A2L")
        self.tabs.addTab(TABSearch(self), "Search")
        self.tabs.addTab(self.listTab, "List")

        #log box
        self.listViewLog = QListWidget()
        self.listViewLog.setFixedHeight(100)
        layoutLog = QVBoxLayout()
        layoutLog.addWidget(self.listViewLog)

        layoutBoxAll = QVBoxLayout()
        layoutBoxAll.addWidget(self.tabs)
        layoutBoxAll.addLayout(layoutLog)

        widget = QWidget()
        widget.setLayout(layoutBoxAll)
        self.setGeometry(300, 300, 650, 600)
        self.setCentralWidget(widget)
        self.show()


    def addLogEntry(self, entry):
        self.listViewLog.addItem(entry)
        self.listViewLog.scrollToBottom()


    def addListItem(self, item):
        self.listTab.addListItem(item)


# Main
app = QApplication(sys.argv)
w = MainWindow()
app.exec()