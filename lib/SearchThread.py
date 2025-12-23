import decimal
import lib.Constants as Constants
from PyQt6.QtCore import QThread, pyqtSignal
from pya2l import model
from enum import Enum


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

        self.a2lsession     = None
        self.search_string  = ""
        self.search_type    = SearchType.NAME


    def run(self):
        if self.a2lsession is None:
            self.logMessage.emit("Search: No database loaded")
            self.finished.emit()
            return

        try:
            if self.search_type == SearchType.NAME:
                self.logMessage.emit(f"Search name: {self.search_string}")
                items = (
                    self.a2lsession.query(model.Measurement)
                        .order_by(model.Measurement.name)
                        .filter(model.Measurement.name.contains(self.search_string))
                        .all()
                )

            elif self.search_type == SearchType.DESC:
                self.logMessage.emit(f"Search description: {self.search_string}")
                items = (
                    self.a2lsession.query(model.Measurement)
                        .order_by(model.Measurement.name)
                        .filter(model.Measurement.longIdentifier.contains(self.search_string))
                        .all()
                )

            elif self.search_type == SearchType.ADDR:
                self.search_string = self.search_string.lower()
                self.logMessage.emit(f"Search address: {self.search_string}")
                items = (
                    self.a2lsession.query(model.Measurement)
                        .order_by(model.Measurement.name)
                        .all()
                )

            else:
                self.logMessage.emit("Search: invalid search type")
                self.finished.emit()
                return

            item_count = 0
            for item in items:
                #if the item has no address ignore it
                if hasattr(item.ecu_address, 'address') == False:
                    continue

                #if searching by address we need to complete the filtering here
                if self.search_type == SearchType.ADDR and self.search_string not in hex(item.ecu_address.address):
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