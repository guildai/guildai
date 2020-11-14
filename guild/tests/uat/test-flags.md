# Test Flags

    >>> cd(example("get-started-use-guild"))

    >>> run("guild run train --test-flags")  # doctest: +REPORT_UDIFF
    ### Script flags for train
    reading flags for main spec 'mnist_mlp_10sec'
    mnist_mlp_10sec.py flags imported for dest 'globals':
      batch_size:
        arg-split: null
        default: 128
        type: number
      epochs:
        arg-split: null
        default: 20
        type: number
      num_classes:
        arg-split: null
        default: 10
        type: number
    ### Script flags for train-args
    reading flags for main spec 'mnist_mlp_args'
    mnist_mlp_args.py flags imported for dest 'args':
      10sec:
        arg-switch: true
        default: false
      activation:
        choices:
        - relu
        - sigmoid
        - tanh
        default: relu
      batch-size:
        default: 128
      dropout:
        default: 0.2
      epochs:
        default: 20
      inner-layers:
        default: 1
      layer-size:
        default: 512
      learning-rate:
        default: 0.001
    ### Script flags for train-config
    flags import disabled - skipping
    flags-dest: globals
    flags-import: yes
    flags:
      batch_size:
        default: 128
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
      epochs:
        default: 20
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
      num_classes:
        default: 10
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

    >>> run("guild run train-args --test-flags")  # doctest: +REPORT_UDIFF
    ### Script flags for train
    reading flags for main spec 'mnist_mlp_10sec'
    mnist_mlp_10sec.py flags imported for dest 'globals':
      batch_size:
        arg-split: null
        default: 128
        type: number
      epochs:
        arg-split: null
        default: 20
        type: number
      num_classes:
        arg-split: null
        default: 10
        type: number
    ### Script flags for train-args
    reading flags for main spec 'mnist_mlp_args'
    mnist_mlp_args.py flags imported for dest 'args':
      10sec:
        arg-switch: true
        default: false
      activation:
        choices:
        - relu
        - sigmoid
        - tanh
        default: relu
      batch-size:
        default: 128
      dropout:
        default: 0.2
      epochs:
        default: 20
      inner-layers:
        default: 1
      layer-size:
        default: 512
      learning-rate:
        default: 0.001
    ### Script flags for train-config
    flags import disabled - skipping
    flags-dest: args
    flags-import: yes
    flags:
      10sec:
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
      activation:
        default: relu
        type:
        required: no
        arg-name:
        arg-skip:
        arg-switch:
        arg-split:
        env-name:
        choices: [relu, sigmoid, tanh]
        allow-other: no
        distribution:
        max:
        min:
        null-label:
      batch-size:
        default: 128
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
      dropout:
        default: 0.2
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
      epochs:
        default: 20
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
      inner-layers:
        default: 1
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
      layer-size:
        default: 512
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
      learning-rate:
        default: 0.001
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
    <exit 0>
