from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QRadioButton, QFileDialog, QLineEdit, QLabel
from lib.LoadA2LThread import LoadA2LThread


class TABA2L(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.parent     = parent
        self.loadThread = LoadA2LThread(self.parent.addLogEntry, self.onFinishedLoading)

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

        #Load button
        self.loadPushButton = QPushButton("Load")
        self.loadPushButton.setFixedHeight(50)
        self.loadPushButton.pressed.connect(self.LoadButtonClick)
        self.mainLayoutBox.addWidget(self.loadPushButton)

        self.setLayout(self.mainLayoutBox)


    def FindButtonClick(self):
        a2lFileName = QFileDialog.getOpenFileName(self, "Open A2L", "", "A2L (*.a2l *.a2ldb)",)
        self.fileEditBox.setText(a2lFileName[0])


    def LoadButtonClick(self):
        self.loadThread.filename = self.fileEditBox.text()
        self.loadThread.start()
        self.loadPushButton.setEnabled(False)


    def onFinishedLoading(self):
        self.parent.a2ldb       = self.loadThread.a2ldb
        self.parent.a2lsession  = self.loadThread.a2lsession
        self.loadPushButton.setEnabled(True)
