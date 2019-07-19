# Initial packages

By default the `packages` command lists packages in the `gpkg`
namespace). We don't have any installed yet so this is an empty list.

    >>> run("guild packages")
    <BLANKLINE>
    <exit 0>

If we use the `-a` option, we get all packages, which at this point
consists of all of the pip packages that are installed in the env.

Note that we're cutting (showing) only col 1 to avoid using any `...`
to match versions and descriptions (`...` matches across lines, which
leaves room for false positives).

    >>> run("guild packages -a", cut=[0]) # doctest: +REPORT_UDIFF
    Jinja2
    Markdown
    MarkupSafe
    PyYAML
    Pygments
    Werkzeug
    Whoosh
    absl-py
    asn1crypto
    bleach
    certifi
    cffi
    chardet
    click
    cryptography
    daemonize
    docutils
    grpcio
    guildai
    idna
    numpy
    pandas
    pip
    pkginfo
    protobuf
    psutil
    pyOpenSSL
    pycparser
    python-dateutil
    pytz
    readme-renderer
    requests
    requests-toolbelt
    scikit-learn
    scikit-optimize
    scipy
    setuptools
    six
    tabview
    tensorboard
    tensorboardX
    tqdm
    twine
    urllib3
    virtualenv
    webencodings
    wheel
    <exit 0>
