from PyQt6.QtCore import QThread, pyqtSignal
from pya2l import DB, model
from pya2l.api import inspect

class LoadA2LThread(QThread):
    logMessage = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, logMessage, finished):
        super().__init__()

        self.logMessage.connect(logMessage)
        self.finished.connect(finished)

        self.a2ldb      = None
        self.a2lsession = None
        self.filename   = ""


    def run(self):
        self.logMessage.emit(f"Loading file: {self.filename}")

        self.a2ldb = DB()

        try:
            self.a2lsession = (
                self.a2ldb.open_existing(self.filename)
            )

            self.logMessage.emit("Database loaded")

        except:
            try:
                self.a2lsession = (
                    self.a2ldb.import_a2l(self.filename)
                )

                self.logMessage.emit("A2L loaded")

            except:
                self.logMessage.emit("Failed to load")

        self.finished.emit()