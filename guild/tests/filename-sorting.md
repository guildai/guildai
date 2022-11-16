# Filename Sorting

Guild sorts file names using `natsort` to ensure that sequences like
`img1`, `img2`, ... `img10` sort in the expected order.

We use the `natsort` project to generate a run with a sequence of
filenames containing number prefixes.

    >>> cd(sample("projects", "natsort"))

Isolate rus.

    >>> set_guild_home(mkdtemp())

Run the operation to generate the files.

    >>> quiet("guild run op.py -y")

Output from `ls`:

    >>> run("guild ls -ng")
    img0
    img1
    img2
    img3
    img4
    img5
    img6
    img7
    img8
    img9
    img10
    img11
    img12
    img13
    img14
    img15
    img16
    img17
    img18
    img19
    <exit 0>

Files returned for view.

    >>> out, exit = run_capture("guild view --test-runs-data")

    >>> (exit, out)
    (0, ...)

    >>> data = json.loads(out)
    >>> len(data)
    1

    >>> for file in data[0]["files"]:
    ...     print(file["path"])
    img0
    img1
    img2
    img3
    img4
    img5
    img6
    img7
    img8
    img9
    img10
    img11
    img12
    img13
    img14
    img15
    img16
    img17
    img18
    img19
    op.py
