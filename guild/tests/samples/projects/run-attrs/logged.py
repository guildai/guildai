import json

from guild import summary

attrs = summary.SummaryWriter(".", filename_suffix=".attrs")
attrs.add_text("logged-1", "green")
attrs.add_text("logged-2", json.dumps({"numbers": [1, 3, 5], "color": "blue"}))
