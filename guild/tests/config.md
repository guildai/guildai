# Guild config

The module `guild.config` handles user config.

    >>> from guild import config

## User config inheritance

User config can use the `extends` construct to extend other config
sections.

The function `_apply_config_inherits` can be used with parsed user
config as a dict. We'll create a helper function to print the resolved
structure.

    >>> def apply(data):
    ...    config._apply_config_inherits(data, "test")
    ...    pprint(data)

NOTE: For the test below, we'll use the naming convention `sN` for
sections, `iN` for section items, and `aN` for item attributes.

A section item may extend other items in the same section.

    >>> apply({
    ...   "s1": {"i1": {"a1": 1, "a2": 2},
    ...          "i2": {"extends": "i1", "a2": 3}}
    ... })
    {'s1': {'i1': {'a1': 1, 'a2': 2},
            'i2': {'a1': 1, 'a2': 3}}}

It may also extend items under the `config` section.

    >>> apply({
    ...   "config": {"i1": {"a1": 1, "a2": 2}},
    ...   "s1": {"i2": {"extends": "i1", "a2": 3}}
    ... })
    {'s1': {'i2': {'a1': 1, 'a2': 3}}}

If the name occurs in both the current section and the `config`
section, the item under the current section is selected.

    >>> apply({
    ...   "config": {"i1": {"a1": 1, "a2": 2}},
    ...   "s1": {"i1": {"a1": 3, "a2": 4},
    ...          "i2": {"extends": "i1", "a2": 5}}
    ... })
    {'s1': {'i1': {'a1': 3, 'a2': 4},
            'i2': {'a1': 3, 'a2': 5}}}

Cycles are silently ignored by dropping the last leg of the cycle.

    >>> apply({
    ...   "s1": {"i1": {"extends": "i1"}}
    ... })
    {'s1': {'i1': {}}}

    >>> apply({
    ...   "s1": {"i1": {"extends": "i2", "a1": 1, "a2": 2},
    ...          "i2": {"extends": "i1", "a2": 3, "a3": 4}}
    ... })
    {'s1': {'i1': {'a1': 1, 'a2': 2, 'a3': 4},
            'i2': {'a1': 1, 'a2': 3, 'a3': 4}}}

    >>> apply({
    ...   "config": {"i1": {"extends": "i2", "a1": 1, "a2": 2},
    ...              "i2": {"extends": "i3", "a1": 3, "a3": 4},
    ...              "i3": {"extends": "i1", "a1": 5}},
    ...   "s1": {"i4": {"extends": "i1", "a1": 6, "a4": 7},
    ...          "i5": {"extends": "i2", "a2": 8, "a5": 9}}
    ... })
    {'s1': {'i4': {'a1': 6, 'a2': 2, 'a3': 4, 'a4': 7},
            'i5': {'a1': 3, 'a2': 8, 'a3': 4, 'a5': 9}}}

If a parent can't be found, `config.ConfigError` is raised.

    >>> apply({
    ...   "s1": {"i1": {"extends": "i2"}}
    ... })
    Traceback (most recent call last):
    ConfigError: cannot find 'i2' in test

## _Config objects

The class `config._Config` can be used to read config data.

    >>> cfg = config._Config(sample("config/remotes.yml"))
    >>> pprint(cfg.read())
    {'remotes': {'v100': {'ami': 'ami-4f62582a',
                          'description': 'V100 GPU running on EC2',
                          'init': 'echo hello',
                          'instance-type': 'p3.2xlarge',
                          'region': 'us-east-2',
                          'type': 'ec2'},
                 'v100x8': {'ami': 'ami-4f62582a',
                            'description': 'V100 x8 running on EC2',
                            'init': 'echo hello there',
                            'instance-type': 'p3.16xlarge',
                            'region': 'us-east-2',
                            'type': 'ec2'}}}
