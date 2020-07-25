# TensorBoard Export Scalars

Create a project to log scalars:

    >>> project = mkdtemp()

    >>> write(path(project, "test.py"), """
    ... val = 1.0
    ... for tag in "foo", "bar":
    ...     for step in range(5,):
    ...         print("step: %i" % step)
    ...         print("%s: %f" % (tag, val))
    ...         val += 1.0
    ... """)

    >>> cd(project)

Run `test.py` a few times.

    >>> quiet("guild -H . run test.py -y")
    >>> quiet("guild -H . run test.py -y")
    >>> quiet("guild -H . run test.py -y")

Use `guild tensorboard` to export scalars - print to output.

    >>> run("guild -H . tensorboard --export-scalars -")
    run,path,tag,value,step
    ...,.guild,foo,1.0,0
    ...,.guild,foo,2.0,1
    ...,.guild,foo,3.0,2
    ...,.guild,foo,4.0,3
    ...,.guild,foo,5.0,4
    ...,.guild,bar,6.0,0
    ...,.guild,bar,7.0,1
    ...,.guild,bar,8.0,2
    ...,.guild,bar,9.0,3
    ...,.guild,bar,10.0,4
    ...,.guild,foo,1.0,0
    ...,.guild,foo,2.0,1
    ...,.guild,foo,3.0,2
    ...,.guild,foo,4.0,3
    ...,.guild,foo,5.0,4
    ...,.guild,bar,6.0,0
    ...,.guild,bar,7.0,1
    ...,.guild,bar,8.0,2
    ...,.guild,bar,9.0,3
    ...,.guild,bar,10.0,4
    ...,.guild,foo,1.0,0
    ...,.guild,foo,2.0,1
    ...,.guild,foo,3.0,2
    ...,.guild,foo,4.0,3
    ...,.guild,foo,5.0,4
    ...,.guild,bar,6.0,0
    ...,.guild,bar,7.0,1
    ...,.guild,bar,8.0,2
    ...,.guild,bar,9.0,3
    ...,.guild,bar,10.0,4
    <exit 0>

Export to file.

    >>> run("guild -H . tensorboard --export-scalars scalars.csv")
    <exit 0>

    >>> run("cat scalars.csv")
    run,path,tag,value,step
    ...,.guild,foo,1.0,0
    ...,.guild,foo,2.0,1
    ...,.guild,foo,3.0,2
    ...,.guild,foo,4.0,3
    ...,.guild,foo,5.0,4
    ...,.guild,bar,6.0,0
    ...,.guild,bar,7.0,1
    ...,.guild,bar,8.0,2
    ...,.guild,bar,9.0,3
    ...,.guild,bar,10.0,4
    ...,.guild,foo,1.0,0
    ...,.guild,foo,2.0,1
    ...,.guild,foo,3.0,2
    ...,.guild,foo,4.0,3
    ...,.guild,foo,5.0,4
    ...,.guild,bar,6.0,0
    ...,.guild,bar,7.0,1
    ...,.guild,bar,8.0,2
    ...,.guild,bar,9.0,3
    ...,.guild,bar,10.0,4
    ...,.guild,foo,1.0,0
    ...,.guild,foo,2.0,1
    ...,.guild,foo,3.0,2
    ...,.guild,foo,4.0,3
    ...,.guild,foo,5.0,4
    ...,.guild,bar,6.0,0
    ...,.guild,bar,7.0,1
    ...,.guild,bar,8.0,2
    ...,.guild,bar,9.0,3
    ...,.guild,bar,10.0,4
    <exit 0>

Export only the first run.

    >>> run("guild -H . tensorboard --export-scalars - 1")
    run,path,tag,value,step
    ...,.guild,foo,1.0,0
    ...,.guild,foo,2.0,1
    ...,.guild,foo,3.0,2
    ...,.guild,foo,4.0,3
    ...,.guild,foo,5.0,4
    ...,.guild,bar,6.0,0
    ...,.guild,bar,7.0,1
    ...,.guild,bar,8.0,2
    ...,.guild,bar,9.0,3
    ...,.guild,bar,10.0,4
    <exit 0>
