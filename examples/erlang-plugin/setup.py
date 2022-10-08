from setuptools import setup

setup(
    name="erlang_guild",
    entry_points={
        "guild.plugins": [
            "erlang_script = erlang_guild.plugins.escript:EScriptPlugin",
        ],
    },
)
