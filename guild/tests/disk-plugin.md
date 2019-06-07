# Disk plugin

The disk plugin is used to read and log disk stats as TF summaries.

    >>> import guild.plugin
    >>> plugin = guild.plugin.for_name("disk")

We can read disk stats using the `read_summary_values` method:

    >>> plugin.read_summary_values(0)
    {}

The initial stats are empty because stats are reported across
intervals. Let's read them again:

    >>> vals = plugin.read_summary_values(0)

Each system is different and some architectures don't support disk
states (e.g. OSX). We need to be explicit about our tests.

    >>> import sys
    >>> platform = sys.platform

Disk stats aren't supported on OSX:

    >>> if sys == "darwin":
    ...   assert len(vals) == 0, vals

They are supported on Linux:

    >>> if sys.platform == "linux2":
    ...   keys = sorted(vals.keys())
    ...   attrs = [key.rsplit("/", 1)[1] for key in keys]
    ...   assert attrs[0] == "rkbps", attrs
    ...   assert attrs[1] == "rps", attrs
    ...   assert attrs[2] == "util", attrs
    ...   assert attrs[3] == "wkbps", attrs
    ...   assert attrs[4] == "wps", attrs

Here we read the first five results and assert their attribute
values. Each value is in the form "sys/DEVICE/ATTTR". As each
system has different devices and names, this is as much as we can
assert generally.
