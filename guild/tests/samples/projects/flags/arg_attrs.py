import argparse

p = argparse.ArgumentParser()

p.add_argument(
    "--str-choice",
    help="Some choices",
    default="A",
    choices=["A", "B", "C"],
    required=True,
    type=str,
)

p.add_argument(
    "--any",
    help="Any type",
)

p.add_argument(
    "--int",
    help="An int",
    required=True,
    type=int,
)

p.add_argument(
    "--float",
    help="A float",
    default=1.123,
    type=float,
)

p.add_argument(
    "--bool",
    help="A bool",
    default=True,
    type=bool,
)

p.add_argument(
    "--unsupported-type",
    help="An unsupported type",
    default=123,
    choices=[123, 456, "foo"],
    required=True,
    type=lambda x: x,
)

print(p.parse_args())

"""

                   if action.help:
        attrs["description"] = action.help
    if action.default is not None:
        attrs["default"] = _ensure_json_encodable(action.default, flag_name)
    if action.choices:
        attrs["choices"] = _ensure_json_encodable(action.choices, flag_name)
    if action.required:
        attrs["required"] = True
    if action.type:
        attrs["type"] = _flag_type_for_action(action.type, flag_name)
    if isinstance(action, argparse._StoreTrueAction):
        attrs["arg-switch"] = True
    elif isinstance(action, argparse._StoreFalseAction):
        attrs["arg-switch"] = False
    if _multi_arg(action):
        attrs["arg-split"] = True

"""
