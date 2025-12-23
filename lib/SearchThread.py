import decimal
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
                search_long = int(self.search_string, 16)
                filter_type = model.Measurement.name.contains("")

            else:
                self.logMessage.emit("Search: invalid search type")
                self.finished.emit()
                return

            self.logMessage.emit(f"Search {self.filter_type_string()} that {self.filter_position_string()} - {self.search_string}")

            #find items that match this description
            items = (
                self.a2lsession.query(model.Measurement)
                    .order_by(model.Measurement.name)
                    .filter(filter_type)
                    .all()
            )

            item_count = 0
            for item in items:
                #if the item has no address ignore it
                if hasattr(item.ecu_address, 'address') == False:
                    continue

                #if searching by address we need to complete the filtering here
                if self.search_type == SearchType.ADDR:
                    if self.search_position == SearchPosition.START and item.ecu_address.address < search_long:
                        continue

                    elif self.search_position == SearchPosition.CONTAIN and item.ecu_address.address != search_long:
                        continue

                    elif  item.ecu_address.address > search_long:
                        continue

                compuMethod = self.a2lsession.query(model.CompuMethod).order_by(model.CompuMethod.name).filter(model.CompuMethod.name == item.conversion).first()
                self.addItem.emit({
                    "Name"          : item.name,
                    "Unit"          : compuMethod.unit,
                    "Equation"      : self.getEquation(item, compuMethod),
                    "Address"       : hex(item.ecu_address.address),
                    "Length"        : Constants.DATA_LENGTH[item.datatype],
                    "Signed"        : Constants.DATA_SIGNED[item.datatype],
                    "Min"           : self.float_to_str(item.lowerLimit),
                    "Max"           : self.float_to_str(item.upperLimit),
                    "Description"   : item.longIdentifier
                })

                item_count += 1

            self.logMessage.emit(f"Found {item_count} items")

        except Exception as e:
            self.logMessage.emit(f"Search: error - {e}")

        self.finished.emit()


    def float_to_str(self, f):
        # create a new context for this task
        ctx = decimal.Context()
        ctx.prec = 5

        """
        Convert the given float to a string,
        without resorting to scientific notation
        """
        d1 = ctx.create_decimal(repr(f))
        return format(d1, 'f')

    def getEquation(self, item, compuMethod):
        if compuMethod.coeffs is None:
            return "x"

        a, b, c, d, e, f = (
            self.float_to_str(compuMethod.coeffs.a),
            self.float_to_str(compuMethod.coeffs.b),
            self.float_to_str(compuMethod.coeffs.c),
            self.float_to_str(compuMethod.coeffs.d),
            self.float_to_str(compuMethod.coeffs.e),
            self.float_to_str(compuMethod.coeffs.f),
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