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
  - [ ] Background pid
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

- [ ] Custom opdef env
