import sys
from handler import handler

print(handler({"bucket": sys.argv[1], "key": sys.argv[2]}, None))
