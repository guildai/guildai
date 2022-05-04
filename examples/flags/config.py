import pprint
import yaml

flags = yaml.safe_load(open("flags.yml"))

pprint.pprint(flags)
