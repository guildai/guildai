# Multi-run Dependencies

    >> cd(sample("projects", "multi-run"))
    >> set_guild_home(mkdtemp())

    >> run("guild run up x=1 --run-id=1 -y")
    >> run("guild run up x=2 --run-id=2 -y")
    >> run("guild run up x=3 --run-id=3 -y")
    >> run("guild run down --run-id=4 -y")
    >> run("guild run down up=1 --run-id=5 -y")
    >> run("guild run down up=1,3 --run-id=6 -y")
    >> run("guild run down up='3 2' --run-id=7 -y")
    >> run("guild runs")
