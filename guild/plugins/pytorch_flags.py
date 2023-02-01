import logging

from .import_argparse_flags_main import ArgparseActionFlagsImporter
from .import_argparse_flags_main import default_flag_attrs_for_argparse_action

log = logging.getLogger("guild.plugins.pytorch_flags")


class PytorchArgparseActions(ArgparseActionFlagsImporter):
    priority = 40

    def flag_attrs_for_argparse_action(self, action, flag_name):
        if _is_pytorch_action(action):
            attrs = default_flag_attrs_for_argparse_action(
                action, flag_name, ignore_unknown_type=True
            )
            _apply_pytorch_argparse_attrs(action, attrs, flag_name)
            return attrs
        return None


def _is_pytorch_action(action):
    try:
        return (
            hasattr(action.type, "__module__") and "pytorch" in action.type.__module__
        )
    except KeyError:
        return False


def _apply_pytorch_argparse_attrs(action, attrs, flag_name):
    assert hasattr(action.type, "__name__"), action
    action_name = action.type.__name__
    if _is_bool_type(action_name):
        attrs["type"] = None
        attrs["default"] = _bool_default(action.default)
    elif action_name == "_int_or_float_type":
        attrs["type"] = "number"
    elif action_name == "_gpus_allowed_type":
        attrs["type"] = "string"
    elif action_name == "_precision_allowed_type":
        attrs["choices"] = [16, 32, 64]
        attrs["type"] = "int"
    else:
        log.warning(
            "unknown pytorch argparse function %s for flag %s: using default attrs",
            action.type,
            flag_name,
        )


def _is_bool_type(action_name):
    return action_name.startswith("str_to_bool")


def _bool_default(x):
    if x is True:
        return "yes"
    if x is False:
        return "no"
    return x
