import json
import pprint
import sys


src = sys.argv[1]
pprint.pprint(json.load(open(src)))
