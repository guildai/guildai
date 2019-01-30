# Scikit optimize

Before running tests with the `skopt` module, let's silence the
warnings from `numpy.core.umath_tests`:

    >>> import warnings
    >>> warnings.filterwarnings("ignore", category=Warning)
    >>> import numpy.core.umath_tests

## Bayesian optimization

Support for Bayesian optimization is provided by `gp_minimize`
function:

    >>> from skopt import gp_minimize

    >>> res = gp_minimize(
    ...     func=lambda *args: 0,
    ...     dimensions=[(-2.0, 2.0)],
    ...     n_calls=1,
    ...     n_random_starts=0,
    ...     x0=[[-1.0], [0.0], [1.0]],
    ...     y0=[-1.0, 0.0, 1.0],
    ...     random_state=66)

    >>> res.x_iters
    [[-1.0], [0.0], [1.0], [-2.0]]
