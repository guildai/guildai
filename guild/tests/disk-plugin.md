# Disk plugin

The disk plugin is used to read and log disk stats as TF summaries.

    >>> import guild.plugin
    >>> plugin = guild.plugin.for_name("disk")

We can read disk stats using the `read_summary_values` method:

    >>> plugin.read_summary_values()
    {}

The initial stats are empty because stats are reported across
intervals. Let's read them again:

    >>> pprint(plugin.read_summary_values())
    {'system/devsda1/rkbps': ...,
     'system/devsda1/rps': ...,
     'system/devsda1/util': ...,
     'system/devsda1/wkbps': ...,
     'system/devsda1/wps': ...,
     'system/devsda2/rkbps': ...,
     'system/devsda2/rps': ...,
     'system/devsda2/util': ...,
     'system/devsda2/wkbps': ...,
     'system/devsda2/wps': ...}
