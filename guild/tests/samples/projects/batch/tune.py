from guild import batch_util

try:
    batch = batch_util.init_batch()
except batch_util.MissingProtoError:
    print("This script must be run as a Guild optimizer")
else:
    proto_flags = batch.proto_run.get("flags", {})
    print("Tune using proto flags: %s" % sorted(proto_flags.items()))
