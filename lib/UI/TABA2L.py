from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLineEdit, QLabel, QCheckBox, QProgressBar
from lib.LoadA2LThread import LoadA2LThread
from lib.ReplaceThread import ReplaceThread


class TABA2L(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.parent     = parent

        #Load
        self.loadThread = LoadA2LThread()
        self.loadThread.logMessage.connect(self.parent.addLogEntry)
        self.loadThread.progressUpdate.connect(self.onProgressUpdate)
        self.loadThread.finished.connect(self.onFinishedLoading)

        self.replaceThread = ReplaceThread(self.parent.addLogEntry, self.parent.getListItem, self.parent.updateListItem, self._replaceFinished)

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

        #Force rebuild checkbox
        self.forceRebuildCheckBox = QCheckBox("Force rebuild of A2L database")
        self.forceRebuildCheckBox.setChecked(False)
        self.mainLayoutBox.addWidget(self.forceRebuildCheckBox)

        #Progress bar
        self.progressBar = QProgressBar()
        self.progressBar.setFixedHeight(25)
        self.progressBar.setVisible(False)
        self.progressBar.setTextVisible(True)
        self.mainLayoutBox.addWidget(self.progressBar)

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
        self.loadPushButton.setEnabled(False)
        self.parent.tabs.setTabEnabled(1, False)
        self.parent.tabs.setTabEnabled(2, False)
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)

        self.loadThread.filename = self.fileEditBox.text()
        self.loadThread.forceRebuild = self.forceRebuildCheckBox.isChecked()
        self.loadThread.start()


    def onProgressUpdate(self, percentage, status_text):
        if percentage == 0:
            # Reset or show indeterminate
            self.progressBar.setRange(0, 100)
            self.progressBar.setValue(0)
        elif percentage < 0:
            # Indeterminate mode (busy indicator)
            self.progressBar.setRange(0, 0)
        else:
            # Normal progress mode
            self.progressBar.setRange(0, 100)
            self.progressBar.setValue(percentage)
        
        self.progressBar.setFormat(status_text)


    def onFinishedLoading(self):
        #overwrite list pid addresses
        if self.overwriteCheckBox.isChecked():
            self.replaceThread.run(self.loadThread.a2lsession, self.parent.a2lsession)

        else:
            self._loadA2LSession()


    def _checkOverwrite(self):
        self.overwriteCheckBox.setEnabled(True if self.parent.a2lsession is not None else False)


    def _loadA2LSession(self):
        #set current a2l database
        self.parent.a2ldb       = self.loadThread.a2ldb
        self.parent.a2lsession  = self.loadThread.a2lsession

        #update layout
        self.loadPushButton.setEnabled(True)
        self.progressBar.setVisible(False)
        self._checkOverwrite()

        # Switch to Search tab if file loaded successfully
        if self.parent.a2lsession is not None:
            self.parent.tabs.setTabEnabled(1, True)
            self.parent.tabs.setTabEnabled(2, True)
            self.parent.tabs.setCurrentIndex(1)
            
            # Check if there's a pending CSV file to load
            if hasattr(self.parent, 'checkAndLoadPendingCSV'):
                self.parent.checkAndLoadPendingCSV()


    def _replaceFinished(self):
        self._loadA2LSession()