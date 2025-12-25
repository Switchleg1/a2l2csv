import subprocess
import sys
from PyQt6.QtCore import QThread, pyqtSignal
from pya2l import DB

class LoadA2LThread(QThread):
    logMessage = pyqtSignal(str)

    def __init__(self):
        super().__init__()

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
            
            # Apply SQLite performance optimizations
            # These pragmas improve query performance on all platforms (Windows, macOS, Linux)
            try:
                self.a2lsession.execute("PRAGMA journal_mode=WAL")
                self.a2lsession.execute("PRAGMA synchronous=NORMAL")
                self.a2lsession.execute("PRAGMA cache_size=-64000")  # 64MB cache
                self.a2lsession.execute("PRAGMA temp_store=MEMORY")
                self.a2lsession.commit()
            except Exception as e:
                # If pragmas fail, log but continue - database will still work
                self.logMessage.emit(f"Note: Could not apply SQLite optimizations: {e}")

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

            except Exception as e:
                self.logMessage.emit(f"Failed to load: {e}")