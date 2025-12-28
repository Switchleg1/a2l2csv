import subprocess
import sys
import os
import logging
import io
import re
import threading
import time
from contextlib import redirect_stdout, redirect_stderr
import lib.Constants as Constants
from PyQt6.QtCore import QThread, pyqtSignal
from pya2l import DB

class LoadA2LThread(QThread):
    logMessage = pyqtSignal(str)
    progressUpdate = pyqtSignal(int, str)  # (percentage, status_text)

    def __init__(self):
        super().__init__()

        self.a2ldb      = None
        self.a2lsession = None
        self.filename   = ""
        self.forceRebuild = False
        self._stop_monitoring = False
        self._monitor_thread = None
        
        # Set up logging handlers immediately upon thread creation
        # This ensures we catch ALL pya2l log messages
        self._setup_pya2l_logging()
    
    def _monitor_file_size(self, db_filename, a2l_file):
        """Monitor the database file size to estimate progress"""
        try:
            # Get the size of the source A2L file
            if os.path.exists(a2l_file):
                a2l_size = os.path.getsize(a2l_file)
            else:
                a2l_size = 1  # Avoid division by zero
            
            print(f"[FileMonitor] A2L file size: {a2l_size} bytes", flush=True)
            
            last_size = 0
            stall_count = 0
            
            while not self._stop_monitoring:
                time.sleep(0.5)  # Check every 500ms
                
                if os.path.exists(db_filename):
                    try:
                        current_size = os.path.getsize(db_filename)
                        
                        # Skip if file is too small (just created, not yet populated)
                        # Wait for at least 100KB to avoid showing high percentage too early
                        if current_size < 102400:  # Less than 100KB
                            continue
                        
                        # Estimate progress based on file size
                        # Database is typically 0.9-1.0x the size of the A2L file (slightly smaller)
                        estimated_final_size = a2l_size * 1.0  # 1:1 ratio based on your data
                        progress_ratio = min(current_size / estimated_final_size, 0.95)  # Cap at 95%
                        # Direct mapping: 0% file = 0% progress, 95% file = 95% progress
                        progress = int(progress_ratio * 100)
                        
                        if current_size != last_size:
                            size_kb = current_size // 1024
                            # Don't print here - it causes recursion with ProgressCapture
                            self.progressUpdate.emit(progress, f"Building database... ({size_kb} KB)")
                            last_size = current_size
                            stall_count = 0
                        else:
                            stall_count += 1
                            # If file hasn't grown in 5 seconds, it might be done
                            if stall_count > 10:
                                break
                    except OSError as e:
                        # File might be locked or temporarily unavailable
                        time.sleep(0.1)
                        continue
                            
        except Exception as e:
            print(f"[FileMonitor] Error: {e}", flush=True)
            import traceback
            traceback.print_exc()


    def _parse_progress_output(self, line):
        """Parse progress information from pya2l console output"""
        # Look for tqdm-style progress bars: "50%|█████     | 500/1000 [00:10<00:10, 50.00it/s]"
        # Or percentage indicators like "Processing: 75%"
        
        # Try to match tqdm format
        tqdm_match = re.search(r'(\d+)%\|', line)
        if tqdm_match:
            percentage = int(tqdm_match.group(1))
            # Don't print here - causes recursion
            self.progressUpdate.emit(percentage, "Importing A2L file...")
            return True
        
        # Try to match simple percentage format
        percent_match = re.search(r'(\d+)%', line)
        if percent_match:
            percentage = int(percent_match.group(1))
            # Don't print here - causes recursion
            self.progressUpdate.emit(percentage, "Processing...")
            return True
        
        # Look for specific pya2l messages
        if "Preprocessing" in line or "preprocessing" in line:
            # Don't print here - causes recursion
            self.progressUpdate.emit(30, "Preprocessing A2L file...")
            return True
        elif "Parsing" in line or "parsing" in line:
            # Don't print here - causes recursion
            self.progressUpdate.emit(60, "Parsing A2L structure...")
            return True
        elif "Creating database" in line or "Populating" in line:
            # Don't print here - causes recursion
            self.progressUpdate.emit(85, "Creating database...")
            return True
        
        return False
    
    def _setup_pya2l_logging(self):
        """Setup logging to capture pya2l progress messages"""
        # Remove any existing handlers first to avoid duplicates
        for logger_name in ['preprocessor', 'a2l', 'pya2l']:
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
        
        class ProgressHandler(logging.Handler):
            def __init__(self, thread):
                super().__init__()
                self.thread = thread
                self.setLevel(logging.INFO)
                
            def emit(self, record):
                try:
                    msg = record.getMessage()
                    print(f"[ProgressHandler] Captured log: {msg}", flush=True)
                    sys.stdout.flush()  # Force immediate output
                    
                    # Parse pya2l log messages to update progress
                    if "Preprocessing and tokenizing" in msg:
                        print(f"[ProgressHandler] Emitting: 20% Preprocessing", flush=True)
                        self.thread.progressUpdate.emit(20, "Preprocessing A2L file...")
                    elif "Start parsing" in msg:
                        print(f"[ProgressHandler] Emitting: 50% Parsing", flush=True)
                        self.thread.progressUpdate.emit(50, "Parsing A2L structure...")
                    elif "Elapsed Time" in msg:
                        # Check if this is after preprocessing or after parsing
                        if "parsing" in msg.lower():
                            print(f"[ProgressHandler] Emitting: 70% Parsing complete", flush=True)
                            self.thread.progressUpdate.emit(70, "Parsing complete...")
                        else:
                            print(f"[ProgressHandler] Emitting: 40% Preprocessing complete", flush=True)
                            self.thread.progressUpdate.emit(40, "Preprocessing complete...")
                    elif "Number of keywords" in msg:
                        print(f"[ProgressHandler] Emitting: 90% Finalizing", flush=True)
                        self.thread.progressUpdate.emit(90, "Finalizing database...")
                except Exception as e:
                    print(f"[ProgressHandler] Error in emit: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
        
        # Get pya2l loggers and add our handler
        handler = ProgressHandler(self)
        for logger_name in ['preprocessor', 'a2l', 'pya2l']:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)
            logger.addHandler(handler)
            print(f"[LoadA2LThread] Added handler to logger: {logger_name}")
            
    def run(self):
        print(f"[LoadA2LThread] Loading file: {self.filename}")
        self.logMessage.emit(f"Loading file: {self.filename}")
        self.progressUpdate.emit(0, "Starting...")

        # Logging handlers were set up in __init__
        # Just ensure they're still active
        for logger_name in ['preprocessor', 'a2l', 'pya2l']:
            logger = logging.getLogger(logger_name)
            if not logger.handlers:
                print(f"[LoadA2LThread] WARNING: No handlers on {logger_name}, re-adding")
                self._setup_pya2l_logging()
                break
        
        self.a2ldb = DB()

        # If force rebuild is checked, delete the .a2ldb file if it exists
        if self.forceRebuild:
            print(f"[LoadA2LThread] Force rebuild is enabled")
            # Handle both .a2l and .a2ldb file extensions
            if self.filename.endswith('.a2l'):
                a2ldb_filename = self.filename + 'db'  # .a2l -> .a2ldb
            elif self.filename.endswith('.a2ldb'):
                a2ldb_filename = self.filename
            else:
                a2ldb_filename = self.filename + '.a2ldb'
            
            print(f"[LoadA2LThread] Target database file: {a2ldb_filename}")
            if os.path.exists(a2ldb_filename):
                try:
                    os.remove(a2ldb_filename)
                    print(f"[LoadA2LThread] Successfully deleted: {a2ldb_filename}")
                    self.logMessage.emit(f"Deleted existing database: {a2ldb_filename}")
                    self.progressUpdate.emit(5, "Deleted existing database")
                except Exception as e:
                    print(f"[LoadA2LThread] ERROR deleting database: {e}")
                    self.logMessage.emit(f"Warning: Could not delete existing database: {e}")

        # Determine the database filename
        if self.filename.endswith('.a2l'):
            db_filename = self.filename + 'db'  # .a2l -> .a2ldb
        elif self.filename.endswith('.a2ldb'):
            db_filename = self.filename
        else:
            db_filename = self.filename + '.a2ldb'
        
        # Check if database already exists
        db_exists = os.path.exists(db_filename)
        
        try:
            # If database exists and we're not forcing rebuild, just open it
            if db_exists and not self.forceRebuild:
                print(f"[LoadA2LThread] Opening existing database: {db_filename}")
                self.progressUpdate.emit(10, "Opening existing database...")
                self.a2lsession = self.a2ldb.open_existing(db_filename)
                
                # Apply SQLite performance optimizations
                if Constants.APPLY_SQL_OPTIMIZATIONS:
                    try:
                        self.a2lsession.execute("PRAGMA journal_mode=WAL")
                        self.a2lsession.execute("PRAGMA synchronous=NORMAL")
                        self.a2lsession.execute("PRAGMA cache_size=-64000")  # 64MB cache
                        self.a2lsession.execute("PRAGMA temp_store=MEMORY")
                        self.a2lsession.commit()
                    except Exception as e:
                        self.logMessage.emit(f"Note: Could not apply SQLite optimizations: {e}")

                self.progressUpdate.emit(100, "Database loaded")
                self.logMessage.emit("Database loaded")
                return
                
        except Exception as e:
            print(f"[LoadA2LThread] Failed to open existing database: {e}")
            self.logMessage.emit(f"Failed to open existing database: {e}")
            # Fall through to rebuild
        
        # If we get here, we need to build/rebuild the database
        try:
            print(f"[LoadA2LThread] Building database from: {self.filename}")
            self.logMessage.emit(f"Wait for database to build - {self.filename}")
            self.progressUpdate.emit(15, "Building database...")
            
            # Close any existing database connection before attempting to delete
            if self.a2lsession is not None:
                print(f"[LoadA2LThread] Closing existing session")
                try:
                    self.a2lsession.close()
                except Exception as e:
                    print(f"[LoadA2LThread] Error closing session: {e}")
                self.a2lsession = None
            
            # Clear the DB object reference
            self.a2ldb = None
            
            # Force garbage collection to release file handles
            import gc
            gc.collect()
            
            # Give the OS a moment to release the file lock
            import time
            time.sleep(0.1)
            
            # Build database directly in thread
            # This works for both PyInstaller executables and regular Python scripts
            # Since we're already in a QThread, this won't block the UI
            
            # Try different encodings in order of likelihood for A2L files
            encodings = ["latin-1", "cp1252", "utf-8", "iso-8859-1"]
            last_error = None
            
            for idx, encoding in enumerate(encodings):
                try:
                    print(f"[LoadA2LThread] Trying encoding {idx+1}/{len(encodings)}: {encoding}")
                    self.logMessage.emit(f"Trying encoding: {encoding}")
                    
                    # Ensure database file doesn't exist before import
                    if os.path.exists(db_filename):
                        print(f"[LoadA2LThread] Database file exists, attempting to delete: {db_filename}")
                        try:
                            os.remove(db_filename)
                            print(f"[LoadA2LThread] Successfully removed database file")
                            self.logMessage.emit(f"Removed existing database before import")
                        except Exception as del_err:
                            print(f"[LoadA2LThread] ERROR: Could not delete {db_filename}: {del_err}")
                            self.logMessage.emit(f"Could not delete {db_filename}: {del_err}")
                            # Don't raise - try to continue anyway
                    
                    self.a2ldb = DB()  # Create fresh DB instance for each attempt
                    
                    # Import from the .a2l file (not .a2ldb)
                    a2l_file = self.filename if self.filename.endswith('.a2l') else self.filename.replace('.a2ldb', '.a2l')
                    print(f"[LoadA2LThread] Importing from: {a2l_file}")
                    
                    # Capture stdout/stderr to parse progress information
                    # Create string buffers to capture output
                    stdout_capture = io.StringIO()
                    stderr_capture = io.StringIO()
                    
                    # We need to capture both stdout and stderr, and also monitor them in real-time
                    # Use a custom writer that both captures and parses
                    class ProgressCapture:
                        def __init__(self, thread, original_stream):
                            self.thread = thread
                            self.original = original_stream
                            self.buffer = []
                            
                        def write(self, text):
                            if text and text.strip():
                                # Parse for progress (but don't print - causes recursion and Unicode errors!)
                                self.thread._parse_progress_output(text)
                            # Don't write to original - causes recursion loop and Unicode encoding errors
                            return len(text)
                        
                        def flush(self):
                            # Don't flush original - not needed since we're not writing to it
                            pass
                    
                    # Replace stdout/stderr temporarily
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    sys.stdout = ProgressCapture(self, old_stdout)
                    sys.stderr = ProgressCapture(self, old_stderr)
                    
                    try:
                        # Start file size monitoring in a separate thread
                        self._stop_monitoring = False
                        self._monitor_thread = threading.Thread(
                            target=self._monitor_file_size,
                            args=(db_filename, a2l_file),
                            daemon=True
                        )
                        self._monitor_thread.start()
                        
                        # Enable console progress bar so pya2l outputs progress
                        self.a2lsession = self.a2ldb.import_a2l(a2l_file, encoding=encoding, progress_bar=True)
                    finally:
                        # Stop monitoring
                        self._stop_monitoring = True
                        if self._monitor_thread:
                            self._monitor_thread.join(timeout=1.0)
                        
                        # Restore original stdout/stderr
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr
                    
                    print(f"[LoadA2LThread] SUCCESS: Loaded with {encoding} encoding")
                    self.progressUpdate.emit(100, f"Successfully loaded with {encoding}")
                    self.logMessage.emit(f"Successfully loaded with {encoding} encoding")
                    break
                except UnicodeDecodeError as e:
                    # Encoding error - immediately try next encoding
                    print(f"[LoadA2LThread] UnicodeDecodeError with {encoding}: {e}")
                    self.logMessage.emit(f"Encoding {encoding} failed, trying next...")
                    last_error = e
                    # Clean up the DB instance
                    self.a2ldb = None
                    self.a2lsession = None
                    continue
                except Exception as e:
                    # Check if it's the "file already exists" error
                    print(f"[LoadA2LThread] Exception with {encoding}: {type(e).__name__}: {e}")
                    if "already exists" in str(e):
                        self.logMessage.emit(f"Database file exists, trying next encoding...")
                        last_error = e
                        self.a2ldb = None
                        self.a2lsession = None
                        continue
                    else:
                        # Other error - might not be encoding related
                        print(f"[LoadA2LThread] Non-recoverable error, stopping encoding attempts")
                        last_error = e
                        break
            
            if self.a2lsession is None:
                print(f"[LoadA2LThread] FAILED: Could not load with any encoding")
                self.progressUpdate.emit(0, "Failed to load")
                raise last_error if last_error else Exception("Failed to load A2L file with any encoding")
            
            print(f"[LoadA2LThread] Finished successfully")
            self.logMessage.emit(f"Finished")

        except Exception as e:
            print(f"[LoadA2LThread] FINAL ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self.progressUpdate.emit(0, "Error")
            self.logMessage.emit(f"Failed to load: {e}")