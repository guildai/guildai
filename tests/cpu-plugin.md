# CPU plugin

The cpu plugin is used to read and log CPU stats as TF summaries.

    >>> import guild.plugin
    >>> plugin = guild.plugin.for_name("cpu")

We can read CPU stats using the `read_summary_values` method:

    >>> plugin.read_summary_values()
    {}

The initial stats are empty because stats are reported across
intervals. Let's read them again:

    >>> pprint(plugin.read_summary_values())
    {'system/cpu/util': ...,
     'system/cpu0/util': ...}
