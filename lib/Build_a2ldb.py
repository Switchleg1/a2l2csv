from pya2l import DB
from sys import argv

if len(argv) != 2:
    print(f"Argument count of: {len(argv)} is invalid, example: python build_a2ldb.py <a2l>")
    exit()

# arguments
A2L_FILENAME     = argv[1]

db = DB()
session = (
    db.import_a2l(A2L_FILENAME, encoding = "latin-1")
)