# Changes

## 0.6.4

- TensorFlow 2 support (beta)
- Refactor publish implementation
  - Publish series of user-facing run files (e.g. run.yml, flags.yml,
    scalars.csv, etc.)
  - Don't publish files by default (can explicitly publish using
    `--files` option)
  - Complete include and exclude support for selecting files to
    publish
  - Include run output in default report
- `select-min` and `select-max` patterns for reducing source file
  selection to a min and max version respectively
- User script exceptions are shown with Guild stack layers removed to
  reduce noise (this behavior can be disabled for additional
  debugging)
- Support for `port` and `connect-timeout` SSH remote attributes

### Fixes

- Import error when using `guild.ipy` (missing click module)
- Cleanup use of labels for batch trials

## 0.6.3

- Early release support for publishing runs
- Early release Notebook support (`guild.ipy` module)
- Renamed `source` to `snapshot-source` to disambiguate from resource
  source config
- Simplified snapshot source config
- Safe guards for default source snapshots (can be overridden by
  adding snapshot-source config)
  - Skip files larger than 1M
  - Don't copy more than 100 files

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
