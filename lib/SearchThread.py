import lib.Helpers as Helpers
import lib.Constants as Constants
from PyQt6.QtCore import QThread, pyqtSignal
from pya2l import model
from enum import Enum


class SearchPosition(Enum):
    START   = 1
    CONTAIN = 2
    END     = 3

class SearchType(Enum):
    NAME    = 1
    DESC    = 2
    ADDR    = 3


class SearchThread(QThread):
    logMessage  = pyqtSignal(str)
    finished    = pyqtSignal()
    addItem     = pyqtSignal(dict)


    def __init__(self, logMessage, addItem, finished):
        super().__init__()

        self.logMessage.connect(logMessage)
        self.addItem.connect(addItem)
        self.finished.connect(finished)

        self.a2lsession         = None
        self.search_string      = ""
        self.search_position    = SearchPosition.CONTAIN
        self.search_type        = SearchType.NAME


    def run(self):
        if self.a2lsession is None:
            self.logMessage.emit("Search: No database loaded")
            self.finished.emit()
            return

        try:
            #get filter type
            filter_type = None
            if self.search_type == SearchType.NAME:
                if self.search_position == SearchPosition.START:
                    filter_type = model.Measurement.name.istartswith(self.search_string)

                elif self.search_position == SearchPosition.CONTAIN:
                    filter_type = model.Measurement.name.icontains(self.search_string)

                else:
                    filter_type = model.Measurement.name.iendswith(self.search_string)

            elif self.search_type == SearchType.DESC:
                if self.search_position == SearchPosition.START:
                    filter_type = model.Measurement.longIdentifier.istartswith(self.search_string)

                elif self.search_position == SearchPosition.CONTAIN:
                    filter_type = model.Measurement.longIdentifier.icontains(self.search_string)

                else:
                    filter_type = model.Measurement.longIdentifier.iendswith(self.search_string)

            elif self.search_type == SearchType.ADDR:
                self.search_string = self.search_string.lower()
                try:
                    search_long = int(self.search_string, 16)
                except ValueError:
                    self.logMessage.emit(f"Search: invalid hex address - {self.search_string}")
                    self.finished.emit()
                    return
                # For address search, we'll handle filtering differently
                # Set a dummy filter that matches everything with an address
                filter_type = None

            else:
                self.logMessage.emit("Search: invalid search type")
                self.finished.emit()
                return

            self.logMessage.emit(f"Search {self.filter_type_string()} that {self.filter_position_string()} - {self.search_string}")

            # For address searches, use a more efficient approach
            if self.search_type == SearchType.ADDR:
                # Query all measurements that have an ECU address
                # We'll filter by address value in the query itself
                query = (
                    self.a2lsession.query(model.Measurement)
                        .join(model.Measurement.ecu_address)
                        .order_by(model.Measurement.name)
                )
                
                # Apply address filtering at database level
                if self.search_position == SearchPosition.START:
                    # "Starts with" for address means >= the search address
                    items = query.filter(model.Measurement.ecu_address.has(
                        model.EcuAddress.address >= search_long
                    )).all()
                elif self.search_position == SearchPosition.CONTAIN:
                    # "Contains" for address means exact match
                    items = query.filter(model.Measurement.ecu_address.has(
                        model.EcuAddress.address == search_long
                    )).all()
                else:
                    # "Ends with" for address means <= the search address
                    items = query.filter(model.Measurement.ecu_address.has(
                        model.EcuAddress.address <= search_long
                    )).all()
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
                conversion_names = set(item.conversion for item in items if hasattr(item, 'conversion'))
                
                # Fetch all needed CompuMethods in a single query
                if conversion_names:
                    compu_method_list = (
                        self.a2lsession.query(model.CompuMethod)
                            .filter(model.CompuMethod.name.in_(conversion_names))
                            .all()
                    )
                    # Build a lookup dictionary for O(1) access
                    compu_methods = {cm.name: cm for cm in compu_method_list}

            item_count = 0
            for item in items:
                # For non-address searches, check if item has an address
                if self.search_type != SearchType.ADDR:
                    if hasattr(item.ecu_address, 'address') == False:
                        continue

                # Get CompuMethod from pre-fetched dictionary
                compuMethod = compu_methods.get(item.conversion)
                if compuMethod is None:
                    # Fallback if conversion not found (shouldn't happen normally)
                    continue

                self.addItem.emit({
                    "Name"          : item.name,
                    "Unit"          : compuMethod.unit,
                    "Equation"      : self.getEquation(item, compuMethod),
                    "Address"       : hex(item.ecu_address.address),
                    "Length"        : Constants.DATA_LENGTH[item.datatype],
                    "Signed"        : Constants.DATA_SIGNED[item.datatype],
                    "Min"           : Helpers.float_to_str(item.lowerLimit),
                    "Max"           : Helpers.float_to_str(item.upperLimit),
                    "Description"   : item.longIdentifier
                })

                item_count += 1

            self.logMessage.emit(f"Found {item_count} items")

        except Exception as e:
            self.logMessage.emit(f"Search: error - {e}")

        self.finished.emit()


    def getEquation(self, item, compuMethod):
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
        
        operation = f"(({f} * [x]) {sign} {c}) / {b}"
        
        if a == "0.0" and d == "0.0" and e=="0.0" and f!="0.0":
            return operation
        else:
            return "x"


    def filter_position_string(self):
        if self.search_position == SearchPosition.START:
            return "starts with"

        elif self.search_position == SearchPosition.CONTAIN:
            return "contains"

        else:
            return "ends with"


    def filter_type_string(self):
        if self.search_type == SearchType.NAME:
            return "name"

        elif self.search_type == SearchType.DESC:
            return "description"

        else:
            return "address"