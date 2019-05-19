# Changes

## 0.6.3

- Early release support for publishing runs
- Early release Notebook support

## 0.6.2

- Improved scheme for capturing script output as scalars
  - Two-group captures used for key/value logging
  - Named group captures
- Show all flags and scalars by default in compare
- Show scalar values in runs info (requireds --scalars option)
  (previously only scalar names were shown)

### Fixes

- Distribution dependency on scikit-optimize

## 0.6.1

### Enhancements

- Windows support for Python 3.5, 3.6, 3.7

### Fixes

- Fix import of boolean flags on Python 3 (report by @OliverRichter)
- Skip all dot directories during source snapshots
- Skip archive diretories during source snapshots

## 0.6.0

This is the baseline release of Guild AI.

Major features:

- Run, track, and compare experiments
- Hyperparameter optimization using grid search, random search, and
  Bayesian optimzation
- Automate model operations and workflows using Guild files
- TensorBoard integration
- Remote training, backups, and restore
