# Notes for op2 refactor

-------------------

Notes Oct 11:

- GPU should be specified when operation is run - should be possible
  to start a run on one GPU, stop it, then restart it on another.

- Generate label from label template

-------------------

## Notes re batch ops

- Use of "batch" in op is a misnomer - op doesn't need to know
  anything about batches

## To Do

- [ ] Batch support
- [ ] Remote support
- [ ] Remove mutation support from `guild.guildfile.OpDef`

- [ ] Args to op2.Operation
  - [ ] Extra attrs
    - [ ] compare
    - [ ] steps
    - [ ] objective
    - [ ] extra attrs from modeldef (is this used? why not from opdef + modeldef?)

- [ ] _flag_map is renamed to flag_map
- [ ] _extra_xxx renamed to extra_xxx - why prefix with 'extra_' ???

- [ ] Misc
  - [ ] Stop after
  - [ ] Background and background pid
  - [ ] Quiet
  - [ ] _maybe_warn_no_wait msg

- [ ] Stage op
- [ ] Stage + start
- [ ] Init trials
- [ ] Restage

- [ ] Null labels in preview

- [ ] Pull support for opref from opdef

- [ ] Error on unknown flag assign
- [ ] Use of force_flags

- [ ] Stoppable opdef

- [ ] Promote OP2-xxx tests
  - [ ] Remove all refs to OP2 env var in tests

- [ ] Remote OP2-xxx targets from Makefile

- [ ] OP2-ops - uses new op module

- [ ] Consider: rename `[xxx_]from_xxx` to `[xxx_]for_xxx`

- [ ] Drop restage from run args

- [ ] Needed flag

- [ ] Custom opdef env - from Guildfile

- [ ] --gup -> CUDA_VISIBLE_DEVICES

- [ ] Batch files

- [ ] Restart
  - [ ] Normal with opdef - with and without flags
  - [ ] Normal without opdef - with and without flags
  - [ ] Batch with opdef - with and without flags
  - [ ] Batch without opdef - with and without flags

- [ ] Run and stage with missing deps
  - [ ] Missing files
  - [ ] Missing operations (different for stage and run)

- [ ] Show pre-emptive resolution of ops and warning when can't resolve

- [ ] New dep to flag scheme
  - [ ] Operation deps always get a flag proxy
  - [ ] Otherwise only if a flag-name attr is defined for the resource
    (or inline source, which is applied to resource)

- [ ] Promote all v2 modules
  - [ ] op_util
  - [ ] op
  - [ ] run_impl
  - [ ] steps_main
  - [ ] random_main

- [ ] Delete replaced modules
  - [ ] deps (replaced by op_dep, verify this)

- [ ] Run search for dead code (vulture?)

- [ ] Remove --init-trials (replaced with --stage-trials)

- [ ] Look for `    >> `, TODO, and op2 refs

- [ ] Remove --restart alias - no point to this

- [ ] Remote support for cat

- [ ] Tests for:
  - [ ] Flag ref in resource name
  - [ ] Flag ref in source URI
  - [ ] Flag ref in source rename pattern
  - [ ] Rename spec with single name val

- [ ] Fix guild view errors

- [ ] --rerun!!
