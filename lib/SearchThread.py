import time
import lib.Helpers as Helpers
import lib.Constants as Constants
from PyQt6.QtCore import QThread, pyqtSignal
from pya2l import model
from lib.Constants import SearchPosition
from lib.Constants import SearchType
from lib.Constants import DBType


class SearchThread(QThread):
    #Signals
    logMessage      = pyqtSignal(str)
    addItem         = pyqtSignal(dict)
    addItemsBatch   = pyqtSignal(list)  # New signal for batch updates
    updateProgress  = pyqtSignal(int, int)
    setupProgress   = pyqtSignal(int, int, int, bool)


    def __init__(self):
        super().__init__()

        self.db_type            = DBType.NONE
        self.a2lsession         = None
        self.csv_name_db        = {}
        self.csv_desc_db        = {}
        self.csv_address_db     = {}

        self.search_string      = ""
        self.search_position    = SearchPosition.CONTAIN
        self.search_type        = SearchType.NAME
        self.item_batch_size    = Constants.SEARCH_BATCH_SIZE
        self.items_left         = Constants.MAX_SEARCH_ITEMS
        self.start_time         = 0
        self.item_count         = 0
        self.results_batch      = []


    def run(self):
        self.start_time     = time.time()
        self.item_count     = 0
        self.results_batch  = []

        if self.db_type == DBType.A2L:
            self._runA2L()

        elif self.db_type == DBType.CSV:
            self._runCSV()

        else:
            self.logMessage.emit("Search: no database loaded")

        #hide progress bar
        self.setupProgress.emit(0, 0, 0, False)


    def _runCSV(self):
        try:
            #get dictionary type
            dict_type = None
            if self.search_type == SearchType.NAME:
                dict_type = self.csv_name_db

            elif self.search_type == SearchType.DESC:
                dict_type = self.csv_desc_db

            elif self.search_type == SearchType.ADDR:
                dict_type = self.csv_address_db
                if self.search_position == SearchPosition.CONTAIN:
                    self.search_position = SearchPosition.EQ

            else:
                self.logMessage.emit("Search: invalid search type")
                return

            if len(dict_type) == 0:
                self.logMessage.emit("Search: no database loaded")
                return

            if self.search_position == SearchPosition.START:
                results_dict = {key: value for key, value in dict_type.items() if key.lower().startswith(self.search_string.lower())}

            elif self.search_position == SearchPosition.CONTAIN:
                results_dict = {key: value for key, value in dict_type.items() if self.search_string.lower() in key.lower()}

            elif self.search_position == SearchPosition.END:
                results_dict = {key: value for key, value in dict_type.items() if key.lower().endswith(self.search_string.lower())}

            else:
                results_dict = {key: value for key, value in dict_type.items() if key.lower() == self.search_string.lower()}

            if results_dict is not None:
                #show progress bar
                self.updateProgress.emit(0, 0)
                self.setupProgress.emit(0, 0, len(results_dict), True)

                for key, value in results_dict.items():
                    item = results_dict[key]

                    #build our result item
                    result_item = {
                        "Name"          : item["Name"],
                        "Unit"          : item["Unit"],
                        "Equation"      : item["Equation"],
                        "Format"        : item["Format"],
                        "Address"       : item["Address"],
                        "Length"        : item["Length"],
                        "Signed"        : item["Signed"],
                        "Min"           : item["ProgMin"],
                        "Max"           : item["ProgMax"],
                        "Description"   : item["Description"]
                    }

                    #if we exceed the max item count return
                    if self._addBatchItem(result_item) == False:
                        self._emitBatch(0)
                        self.logMessage.emit(f"Max items found {self.item_count} in {self._elapsedTime():.2f} seconds")
                        return

                #emit all remaining items from batch
                self._emitBatch(0)

                self.logMessage.emit(f"Found {self.item_count} items in {self._elapsedTime():.2f} seconds")

        except Exception as e:
            self.logMessage.emit(f"Failed after {self._elapsedTime():.2f} seconds - {e}")


    def _runA2L(self):
        if self.a2lsession is None:
            self.logMessage.emit("Search: no database loaded")
            return

        try:
            #get filter type
            filter_type = None
            if self.search_type == SearchType.NAME:
                if self.search_position == SearchPosition.START:
                    filter_type = model.Measurement.name.istartswith(self.search_string)

                elif self.search_position == SearchPosition.CONTAIN:
                    filter_type = model.Measurement.name.icontains(self.search_string)

                elif self.search_position == SearchPosition.END:
                    filter_type = model.Measurement.name.iendswith(self.search_string)

                else:
                    filter_type = model.Measurement.name == self.search_string

            elif self.search_type == SearchType.DESC:
                if self.search_position == SearchPosition.START:
                    filter_type = model.Measurement.longIdentifier.istartswith(self.search_string)

                elif self.search_position == SearchPosition.CONTAIN:
                    filter_type = model.Measurement.longIdentifier.icontains(self.search_string)

                elif self.search_position == SearchPosition.END:
                    filter_type = model.Measurement.longIdentifier.iendswith(self.search_string)

                else:
                    filter_type = model.Measurement.longIdentifier == self.search_string

            elif self.search_type == SearchType.ADDR:
                self.search_string = self.search_string.lower()
                try:
                    search_long = int(self.search_string, 16)
                except ValueError:
                    self.logMessage.emit(f"Search: invalid hex address - {self.search_string}")
                    return
                # For address search, we'll handle filtering differently
                # Set a dummy filter that matches everything with an address
                filter_type = None

            else:
                self.logMessage.emit("Search: invalid search type")
                return

            self.logMessage.emit(f"Search {self._filterTypeString()} that {self._filterPositionString()} - {self.search_string}")

            # For address searches, use a more efficient approach
            if self.search_type == SearchType.ADDR:
                # Use a subquery approach which is much faster on SQLite/macOS
                # This avoids the expensive join operation
                from sqlalchemy import select
                
                # Create subquery to get measurement RIDs with matching addresses
                # EcuAddress._measurement_rid references Measurement.rid
                if self.search_position == SearchPosition.START:
                    # "Starts with" for address means >= the search address
                    address_subquery = (
                        select(model.EcuAddress._measurement_rid)
                        .where(model.EcuAddress.address >= search_long)
                    )
                elif self.search_position == SearchPosition.CONTAIN or self.search_position == SearchPosition.EQ:
                    # "Contains" for address means exact match
                    address_subquery = (
                        select(model.EcuAddress._measurement_rid)
                        .where(model.EcuAddress.address == search_long)
                    )
                else:
                    # "Ends with" for address means <= the search address
                    address_subquery = (
                        select(model.EcuAddress._measurement_rid)
                        .where(model.EcuAddress.address <= search_long)
                    )
                
                # Query measurements using the subquery
                items = (
                    self.a2lsession.query(model.Measurement)
                        .filter(model.Measurement.rid.in_(address_subquery))
                        .order_by(model.Measurement.name)
                        .all()
                )
            else:
                # For name and description searches, use the original approach
                items = (
                    self.a2lsession.query(model.Measurement)
                        .order_by(model.Measurement.name)
                        .filter(filter_type)
                        .all()
                )

            # Pre-fetch all CompuMethods at once to avoid N+1 query problem
            # This dramatically improves performance for large result sets
            compu_methods = {}
            if items:
                # Get unique conversion names from all items
                conversion_names = set(item.conversion for item in items if hasattr(item, 'conversion') and item.conversion)
                
                # Fetch all needed CompuMethods in a single query
                if conversion_names:
                    compu_method_list = (
                        self.a2lsession.query(model.CompuMethod)
                            .filter(model.CompuMethod.name.in_(conversion_names))
                            .all()
                    )
                    # Build a lookup dictionary for O(1) access
                    compu_methods = {cm.name: cm for cm in compu_method_list}

                #show progress bar
                self.updateProgress.emit(0, 0)
                self.setupProgress.emit(0, 0, len(items), True)

            for item in items:
                # For non-address searches, check if item has an address
                # Address searches already filtered by address, so skip this check
                if self.search_type != SearchType.ADDR:
                    if not hasattr(item, 'ecu_address') or not hasattr(item.ecu_address, 'address'):
                        continue

                # Skip items without conversion (no CompuMethod means we can't display properly)
                if not hasattr(item, 'conversion') or not item.conversion:
                    continue

                # Get CompuMethod from pre-fetched dictionary
                compuMethod = compu_methods.get(item.conversion)
                if compuMethod is None:
                    # Skip if conversion not found
                    continue

                #build format string
                try:
                    format_precision = int(compuMethod.format.split(".")[-1].lstrip().rstrip())

                    if format_precision > Constants.FORMAT_PRECISION_LIMIT:
                        decimaformat_precisionl_places = Constants.FORMAT_PRECISION_LIMIT

                    format_str = f"%01.{format_precision}f"

                except:
                    format_str = "%01.0f"

                #build our result item
                result_item = {
                    "Name"          : item.name,
                    "Unit"          : compuMethod.unit,
                    "Equation"      : self._getEquation(item, compuMethod),
                    "Format"        : format_str,
                    "Address"       : hex(item.ecu_address.address),
                    "Length"        : Constants.DATA_LENGTH[item.datatype],
                    "Signed"        : Constants.DATA_SIGNED[item.datatype],
                    "Min"           : Helpers.float_to_str(item.lowerLimit),
                    "Max"           : Helpers.float_to_str(item.upperLimit),
                    "Description"   : item.longIdentifier
                }

                #if we exceed the max item count return
                if self._addBatchItem(result_item) == False:
                    self._emitBatch(0)
                    self.logMessage.emit(f"Max items found {self.item_count} in {self._elapsedTime():.2f} seconds")
                    return

            #emit all remaining items from batch
            self._emitBatch(0)

            self.logMessage.emit(f"Found {self.item_count} items in {self._elapsedTime():.2f} seconds")

        except Exception as e:
            self.logMessage.emit(f"Failed after {self._elapsedTime():.2f} seconds - {e}")


    def _getEquation(self, item, compuMethod):
        if compuMethod.coeffs is None:
            return "x"

        a, b, c, d, e, f = (
            Helpers.float_to_str(compuMethod.coeffs.a),
            Helpers.float_to_str(compuMethod.coeffs.b),
            Helpers.float_to_str(compuMethod.coeffs.c),
            Helpers.float_to_str(compuMethod.coeffs.d),
            Helpers.float_to_str(compuMethod.coeffs.e),
            Helpers.float_to_str(compuMethod.coeffs.f),
        )

        sign = '-'
        if c[0] == '-':
            c = c[1:]
            sign = '+'

        operation = f"(({f} * x) {sign} {c}) / {b}"
        
        if a == "0.0" and d == "0.0" and e=="0.0" and f!="0.0":
            return operation
        else:
            return "x"


    def _filterPositionString(self):
        if self.search_position == SearchPosition.START:
            return "starts with"

        elif self.search_position == SearchPosition.CONTAIN:
            return "contains"

        else:
            return "ends with"


    def _filterTypeString(self):
        if self.search_type == SearchType.NAME:
            return "name"

        elif self.search_type == SearchType.DESC:
            return "description"

        else:
            return "address"


    def _addBatchItem(self, item):
        self.item_count += 1

        # Emit single item if connected
        self.addItem.emit(item)
                
        # Emit batch when it reaches batch_size
        self.results_batch.append(item)
        self._emitBatch(Constants.SEARCH_BATCH_SIZE)

        #quit if the items count has been exceeded
        self.items_left -= 1
        if self.items_left < 0:
            return False

        return True


    def _emitBatch(self, batch_size):
        if len(self.results_batch) >= batch_size:
            #update search results
            self.addItemsBatch.emit(self.results_batch)
            self.results_batch = []

            #update progress bar
            self.updateProgress.emit(0, self.item_count)


    def _elapsedTime(self):
        return time.time() - self.start_time