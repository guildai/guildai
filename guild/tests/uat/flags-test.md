# Flags Test

    >>> cd(example("api"))

    >>> run("guild run op --test-flags")  # doctest: +REPORT_UDIFF
    ### Script flags for op
    reading flags for main spec 'op'
    op.py does not import argparse - assuming globals
    op.py flags imported for dest 'globals':
      x:
        arg-split: null
        default: 1.0
        type: number
    ### Script flags for summary
    reading flags for main spec 'summary'
    summary.py imports argparse - assuming args
    summary.py flags imported for dest 'args':
      min-loss:
        default: -0.2
      output:
        default: .
      use-marked:
        arg-switch: true
        default: false
    flags-dest: globals
    flags-import: [x]
    flags:
      x:
        default: 1.0
        type: number
        required: no
        arg-name:
        arg-skip:
        arg-switch:
        arg-split:
        env-name:
        choices: []
        allow-other: no
        distribution:
        max:
        min:
        null-label:
    <exit 0>

    >>> run("guild run summary --test-flags")  # doctest: +REPORT_UDIFF
    ### Script flags for op
    reading flags for main spec 'op'
    op.py does not import argparse - assuming globals
    op.py flags imported for dest 'globals':
      x:
        arg-split: null
        default: 1.0
        type: number
    ### Script flags for summary
    reading flags for main spec 'summary'
    summary.py imports argparse - assuming args
    summary.py flags imported for dest 'args':
      min-loss:
        default: -0.2
      output:
        default: .
      use-marked:
        arg-switch: true
        default: false
    flags-dest: args
    flags-import: [use-marked, min-loss]
    flags:
      min-loss:
        default: -0.2
        type:
        required: no
        arg-name:
        arg-skip:
        arg-switch:
        arg-split:
        env-name:
        choices: []
        allow-other: no
        distribution:
        max:
        min:
        null-label:
      use-marked:
        default: no
        type:
        required: no
        arg-name:
        arg-skip:
        arg-switch: yes
        arg-split:
        env-name:
        choices: []
        allow-other: no
        distribution:
        max:
        min:
        null-label:
    <exit 0>
