# <Test topic>

<Describe the facility being tested. The initial description should
read more like user facing documentation than implementation
details. Details, including specific functionality and perhaps
implementation details (where appropriate) are described throughout
the document, using headers as needed to structure the narrative.>

These tests use the `<project-dir>` project.

    >>> use_project("optimizers")

<If needed make some assertions about the project and
environment. These should be meaningful tests and not copypasta.>

    >>> run("guild runs")
    <exit 0>

    >>> find(".")
    batch_fail.py
    ...
    trial_fail.py

</...>

## Heading 1

<Summaries what's being tested in this section. If the doc is simple,
omit headings altogether.>

<Use Guild commands via `run()` to illustate points.>

    >>> run("guild run echo.py -y")
    1.0 2 'a'

<Results from `run()` always contain `<exit N>` where `N` is the
process exit code. If the expected code is `0` (typical as we
generally run tests that we expect to succeed) you can omit the last
line of output. If the expected result is non-zero, the last line must
be included (unless otherwise ignored with `...`)>

## Heading 2

<Next section summary, etc.>
