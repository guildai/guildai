# Batch Preview

Create a simply script to test.

    >>> project = mkdtemp()

    >>> cd(project)

    >>> write(path(project, "test.py"), """
    ... x = 1
    ... y = 2
    ... print(x + y)
    ... """)

    >>> run("guild run test.py -y")
    3
    <exit 0>

Preview a normal batch.

    >>> run("guild run test.py x=[1,2] y=[2,3]", timeout=2)
    You are about to run test.py as a batch (4 trials)
      x: [1, 2]
      y: [2, 3]
    Continue? (Y/n)
    <exit -9>

Specify max trials with a normal batch - max trials less than full
trial count.

    >>> run("guild run test.py x=[1,2] y=[2,3] --max-trials 3", timeout=2)
    You are about to run test.py as a batch (3 trials)
      x: [1, 2]
      y: [2, 3]
    Continue? (Y/n)
    <exit -9>

Specify max trials with a normal batch - max trials greater than full
trial count.

    >>> run("guild run test.py x=[1,2] y=[2,3] --max-trials 5", timeout=2)
    You are about to run test.py as a batch (4 trials)
      x: [1, 2]
      y: [2, 3]
    Continue? (Y/n)
    <exit -9>

Random batch:

    >>> run("guild run test.py x=[1:100] --max-trials 5", timeout=3)
    You are about to run test.py with random search (max 5 trials)
      x: [1:100]
      y: 2
    Continue? (Y/n)
    <exit -9>

Optimizer with default objective:

    >>> run("guild run test.py x=[1:100] -o gp", timeout=3)
    You are about to run test.py with 'skopt:gp' optimizer (max 20 trials, minimize loss)
      x: [1:100]
      y: 2
    Optimizer flags:
      acq-func: gp_hedge
      kappa: 1.96
      noise: gaussian
      random-starts: 3
      xi: 0.05
    Continue? (Y/n)
    <exit -9>

Optimizer with explict objective:

    >>> run("guild run test.py x=[1:100] -o gbrt -X foo -m10", timeout=3)
    You are about to run test.py with 'skopt:gbrt' optimizer (max 10 trials, maximize foo)
      x: [1:100]
      y: 2
    Optimizer flags:
      kappa: 1.96
      random-starts: 3
      xi: 0.05
    Continue? (Y/n)
    <exit -9>

Preview batch files:

    >>> write(path(project, "trials-1.csv"), """x
    ... 1
    ... 2
    ... 3
    ... """)

    >>> run("guild run test.py @trials-1.csv", timeout=3)
    You are about to run test.py as a batch (3 trials) (flags below
    used unless specified in batch trial)
      x: 1
      y: 2
    Continue? (Y/n)
    <exit -9>

Preview with batch file and flag list:

    >>> run("guild run test.py @trials-1.csv y=[4,5]", timeout=3)
    You are about to run test.py as a batch (6 trials) (flags below
    used unless specified in batch trial)
      x: 1
      y: [4, 5]
    Continue? (Y/n)
    <exit -9>

Preview with two batch files:

    >>> write(path(project, "trials-2.csv"), """x,y
    ... 4,5
    ... 5,6
    ... """)

    >>> run("guild run test.py @trials-1.csv @trials-2.csv", timeout=3)
    You are about to run test.py as a batch (5 trials) (flags below
    used unless specified in batch trial)
      x: 1
      y: 2
    Continue? (Y/n)
    <exit -9>
