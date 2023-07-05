# Summary Utils

The tests below use a plugin type that prints wrapped scalar
information.

    >>> from guild.plugins.summary_util import SummaryPlugin

    >>> class EntryPointProxy(object):
    ...     def __init__(self, name):
    ...         self.name = name

    >>> class Plugin(SummaryPlugin):
    ...     def __init__(self, name):
    ...         super(Plugin, self).__init__(EntryPointProxy(name))
    ...
    ...     def _handle_guild_scalar(self, add_scalar, tag, value, step=None):
    ...         self._handle_default_scalar(add_scalar, tag, value, step)
    ...
    ...     def _handle_tbx_scalar(self, add_scalar, tag, value, global_step=None):
    ...         self._handle_default_scalar(add_scalar, tag, value, global_step)
    ...
    ...     def _handle_default_scalar(self, add_scalar, tag, value, step=None):
    ...         print("%s plugin got scalar %s=%s (step %s)"
    ...               % (self.name, tag, value, step or 0))
    ...

Helper to read and print scalars from a directory.

    >>> from guild.tfevent import EventReader

    >>> def print_scalars(dir):
    ...     events = EventReader(dir)
    ...     for event in events:
    ...         print(event)

## Patch Guild Summary Writer

Create a plugin that patches the Guild summary writer.

    >>> plugin = Plugin("guild-summary")
    >>> wrapper = plugin._patch_guild_summary()

Create a Guild summary writer. This object is patched by the plugin.

    >>> from guild.summary import SummaryWriter as GuildSummaryWriter
    >>> logdir = mkdtemp()
    >>> summaries = GuildSummaryWriter(logdir)

Log some scalars. Each call to `add_scalar` is also handled by the
plugin, which prints the values.

    >>> summaries.add_scalar("foo", 1.1)
    guild-summary plugin got scalar foo=1.1 (step 0)

    >>> summaries.add_scalar("bar", 2.2, 1)
    guild-summary plugin got scalar bar=2.2 (step 1)

    >>> summaries.add_scalar("baz", 3.3, step=2)
    guild-summary plugin got scalar baz=3.3 (step 2)

    >>> summaries.close()

Show the scalars from the TF event files in the log dir.

    >>> print_scalars(logdir)
    summary {
      value {
        tag: "foo"
        simple_value: 1.1
      }
    }
    <BLANKLINE>
    step: 1
    summary {
      value {
        tag: "bar"
        simple_value: 2.2
      }
    }
    <BLANKLINE>
    step: 2
    summary {
      value {
        tag: "baz"
        simple_value: 3.3
      }
    }

Unwrap patched method.

    >>> wrapper.unwrap()

## Patch TensorboardX

Create a plugin that patches tensorboardX scalar support.

    >>> plugin = Plugin("tbx-summary")
    >>> wrapper = plugin._try_patch_tensorboardX()

Create a tensorboardX summary writer.

    >>> from tensorboardX import SummaryWriter as TbxSummaryWriter
    >>> logdir = mkdtemp()
    >>> summaries = TbxSummaryWriter(logdir)

Log some scalars.

    >>> summaries.add_scalar("foo", 1.12)
    tbx-summary plugin got scalar foo=1.12 (step 0)

    >>> summaries.add_scalar("bar", 2.23, 1)
    tbx-summary plugin got scalar bar=2.23 (step 1)

    >>> summaries.add_scalar("baz", 3.34, global_step=2)
    tbx-summary plugin got scalar baz=3.34 (step 2)

    >>> summaries.close()

Show the scalars from the TF event files in the log dir.

    >>> print_scalars(logdir)
    wall_time: ...
    summary {
      value {
        tag: "foo"
        simple_value: 1.12
      }
    }
    <BLANKLINE>
    wall_time: ...
    step: 1
    summary {
      value {
        tag: "bar"
        simple_value: 2.23
      }
    }
    <BLANKLINE>
    wall_time: ...
    step: 2
    summary {
      value {
        tag: "baz"
        simple_value: 3.34
      }
    }

Unwrap patched method.

    >>> wrapper.unwrap()
