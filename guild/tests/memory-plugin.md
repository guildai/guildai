# Memory plugin

The memory plugin is used to read and log memory stats as TF
summaries.

    >>> import guild.plugin
    >>> plugin = guild.plugin.for_name("memory")

We can read memory stats using the `read_summary_values` method:

    >>> pprint(plugin.read_summary_values())
    {'system/mem_free': ...,
     'system/mem_total': ...,
     'system/mem_used': ...,
     'system/mem_util': ...,
     'system/swap_free': ...,
     'system/swap_total': ...,
     'system/swap_used': ...,
     'system/swap_util': ...}
