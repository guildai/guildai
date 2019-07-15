import pprint
import yaml

f = open("config.yml")
cfg = yaml.safe_load(f)
pprint.pprint(cfg)
