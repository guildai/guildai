import pprint
import sys

import yaml


src = sys.argv[1]
pprint.pprint(yaml.safe_load(open(src)))
