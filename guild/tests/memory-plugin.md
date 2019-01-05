# Memory plugin

The memory plugin is used to read and log memory stats as TF
summaries.

    >>> import guild.plugin
    >>> plugin = guild.plugin.for_name("memory")

We can read memory stats using the `read_summary_values` method:

    >>> pprint(plugin.read_summary_values(0))
    {'sys/mem_free': ...,
     'sys/mem_total': ...,
     'sys/mem_used': ...,
     'sys/mem_util': ...,
     'sys/swap_free': ...,
     'sys/swap_total': ...,
     'sys/swap_used': ...,
     'sys/swap_util': ...}
