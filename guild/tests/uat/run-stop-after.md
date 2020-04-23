# Run stop after

    >>> cd(example("hello"))

    >>> run("guild run repeat.py repeat=6 --stop-after 0.01 -y", ignore="Refreshing")
    Hello Guild!
    Hello Guild!
    Hello Guild!
    Hello Guild!
    Hello Guild!
    Stopping process early (pid ...) - 0.1 minute(s) elapsed
    <exit ...>
