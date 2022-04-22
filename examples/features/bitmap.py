feature_count = 5
features = 0


def feature_enabled(bitmap, feature_bit):
    return bool(bitmap & (1 << feature_bit))


for feature_bit in range(feature_count):
    print("feature %s: %s" % (feature_bit, feature_enabled(features, feature_bit)))
