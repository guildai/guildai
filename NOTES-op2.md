# Notes for op2 refactor

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
