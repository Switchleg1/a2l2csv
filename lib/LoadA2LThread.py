import subprocess
import sys
from PyQt6.QtCore import QThread, pyqtSignal
from pya2l import DB

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
                self.logMessage.emit(f"Wait for database to build - {self.filename}")

                command = [
                    sys.executable,         # Path to the Python executable
                    "lib/Build_a2ldb.py",   # The script to run
                    self.filename,          # Filename
                ]

                process = subprocess.Popen(command)
                stdout, stderr = process.communicate()
                print("Standard Output:", stdout)
                print("Standard Error:", stderr)
                print("Return Code:", process.returncode)

                self.a2lsession = (
                    self.a2ldb.open_existing(self.filename)
                )

                self.logMessage.emit(f"Finished")

            except:
                self.logMessage.emit("Failed to load")

        self.finished.emit()