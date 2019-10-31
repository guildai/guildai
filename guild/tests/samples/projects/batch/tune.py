from guild import batch_util

try:
    batch_run = batch_util.batch_run()
except batch_util.CurrentRunNotBatchError:
    print("This script must be run as a Guild optimizer")
else:
    proto_flags = batch_run.batch_proto.get("flags", {})
    print("Tune using proto flags: %s" % sorted(proto_flags.items()))
