# View after logreg train

Guild View supports a `--test` option, which starts the serve, prints
status, and exits.

    >>> run("guild view --test")
    Running Guild View at http://...
    Testing http://.../runs
     - Got 1 Guild run(s)
    Initializing TensorBoard at http://.../tb/0/
    Testing http://.../tb/0/data/runs
     - Got 2 TensorBoard run(s)
    <exit 0>
