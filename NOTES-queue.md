# Queues

## To Do

- [ ] Tests for source code handling on restarts:

    - [ ] Never replace sourcecode on a restart
    - [ ] Prepend sourcecode dir to op_main Python path

## Notes

### --start vs --restart

I think we can get away with renaming `--restart` to `--start`. The
two options are identical in meaning.

### Rename --stage-pending to --stage

The stage pending is a more common use case. We should rename --stage
to --stage-dir.
