# Op refs

Op refs are stored per run as a reference to the originating
operation. Support for op refs is provided by the `opdef.OpRef` class.

    >>> from guild.opref import OpRef

An op ref consists of 5 parts, each corresponding to an opref
attribute.

 - Package type (`pkg_type`)
 - Package name (`pkg_name`)
 - Package version (`pkg_version`)
 - Model name (`model_name`)
 - Operation name (`op_name`)

Guild supports a number of operation package types:

 - `guildfile`
 - `package`
 - `script`

Each package type applies op ref attribute differently. The table
below describes the differences.

| `pkg_type` | `pkg_name`     | `pkg_version` | `model_name` | `op_name        |
|------------|----------------|---------------|--------------|-----------------|
| guildfile  | guild.yml path | guild.yml md5 | model name   | op name         |
| script     | Script dir     | empty         | empty        | script basename |
| package    | pkg name       | pkg version   | model name   | op name         |

## Guild files

    >>> opref = OpRef("guildfile", "/foo/guild.yml", "", "m1", "op1")

    >>> opref
    OpRef(pkg_type='guildfile',
          pkg_name='/foo/guild.yml',
          pkg_version='',
          model_name='m1',
          op_name='op1')

    >>> opref.to_opspec()
    'm1:op1'

## Scripts

    >>> opref = OpRef("script", "/foo/bar", "", "", "train.py")

    >>> opref
    OpRef(pkg_type='script',
          pkg_name='/foo/bar',
          pkg_version='',
          model_name='',
          op_name='train.py')

    >>> opref.to_opspec(cwd="")
    '/foo/bar/train.py'

    >>> opref.to_opspec(cwd="/foo/bar")
    'train.py'
