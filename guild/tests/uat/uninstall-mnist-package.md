# Uninstall `gpkg.mnist` package

We can remove an installed package using `uninstall` (which is a
synonym for `packages delete`). In this case we'll uninstall `mnist`.

    >>> run("guild uninstall gpkg.mnist -y")
    Uninstalling gpkg.mnist-...:
    Successfully uninstalled gpkg.mnist-...
    <exit 0>

Note that we're not translating pip output generated here - the `gpkg`
namespace leaks through. This is not ideal.
