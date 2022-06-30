---
doctest: -PY2
---

# PyTorch Lightning Example

Use the `pytorch-lightning` example.

    >>> cd(example("pytorch-lightning"))

Show script help.

    >>> run("guild run mnist.py --help-op",
    ...     env={"NO_IMPORT_FLAGS_CACHE": "1"})  # doctest: +REPORT_UDIFF -PY35 -PY2 -PY36
    Usage: guild run [OPTIONS] mnist.py [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      accelerator                     Supports passing different accelerator types
                                      ("cpu", "gpu", "tpu", "ipu", "hpu", "auto")
                                      as well as custom accelerator instances. ..
                                      deprecated:: v1.5 Passing training
                                      strategies (e.g., 'ddp') to ``accelerator``
                                      has been deprecated in v1.5.0 and will be
                                      removed in v1.7.0. Please use the
                                      ``strategy`` argument instead.
    <BLANKLINE>
      accumulate_grad_batches         Accumulates grads every k batches or as set
                                      up in the dict. Default: ``None``.
    <BLANKLINE>
      amp_backend                     The mixed precision backend to use ("native"
                                      or "apex"). Default: ``'native''``. (default
                                      is native)
    <BLANKLINE>
      amp_level                       The optimization level to use (O1, O2,
                                      etc...). By default it will be set to "O2"
                                      if ``amp_backend`` is set to "apex".
    <BLANKLINE>
      auto_lr_find                    If set to True, will make trainer.tune() run
                                      a learning rate finder, trying to optimize
                                      initial learning for faster convergence.
                                      trainer.tune() method will set the suggested
                                      learning rate in self.lr or
                                      self.learning_rate in the LightningModule.
                                      To use a different key set a string instead
                                      of True with the key name. Default:
                                      ``False``. (default is 'no')
    <BLANKLINE>
      auto_scale_batch_size           If set to True, will `initially` run a batch
                                      size finder trying to find the largest batch
                                      size that fits into memory. The result will
                                      be stored in self.batch_size in the
                                      LightningModule. Additionally, can be set to
                                      either `power` that estimates the batch size
                                      through a power search or `binsearch` that
                                      estimates the batch size through a binary
                                      search. Default: ``False``. (default is
                                      'no')
    <BLANKLINE>
      auto_select_gpus                If enabled and ``gpus`` or ``devices`` is an
                                      integer, pick available gpus automatically.
                                      This is especially useful when GPUs are
                                      configured to be in "exclusive mode", such
                                      that only one process at a time can access
                                      them. Default: ``False``. (default is 'no')
    <BLANKLINE>
      benchmark                       The value (``True`` or ``False``) to set
                                      ``torch.backends.cudnn.benchmark`` to. The
                                      value for ``torch.backends.cudnn.benchmark``
                                      set in the current session will be used
                                      (``False`` if not manually set). If :paramre
                                      f:`~pytorch_lightning.trainer.Trainer.determ
                                      inistic` is set to ``True``, this will
                                      default to ``False``. Override to manually
                                      set a different value. Default: ``None``.
    <BLANKLINE>
      check_val_every_n_epoch         Check val every n train epochs. Default:
                                      ``1``. (default is 1)
    <BLANKLINE>
      checkpoint_callback             If ``True``, enable checkpointing. Default:
                                      ``None``. .. deprecated:: v1.5
                                      ``checkpoint_callback`` has been deprecated
                                      in v1.5 and will be removed in v1.7. Please
                                      consider using ``enable_checkpointing``
                                      instead.
    <BLANKLINE>
      default_root_dir                Default path for logs and weights when no
                                      logger/ckpt_callback passed. Default:
                                      ``os.getcwd()``. Can be remote file paths
                                      such as `s3://mybucket/path` or
                                      'hdfs://path/'
    <BLANKLINE>
      detect_anomaly                  Enable anomaly detection for the autograd
                                      engine. Default: ``False``. (default is
                                      'no')
    <BLANKLINE>
      deterministic                   If ``True``, sets whether PyTorch operations
                                      must use deterministic algorithms. If not
                                      set, defaults to ``False``. Default:
                                      ``None``.
    <BLANKLINE>
      devices                         Will be mapped to either `gpus`,
                                      `tpu_cores`, `num_processes` or `ipus`,
                                      based on the accelerator type.
    <BLANKLINE>
      enable_checkpointing            If ``True``, enable checkpointing. It will
                                      configure a default ModelCheckpoint callback
                                      if there is no user-defined ModelCheckpoint
                                      in :paramref:`~pytorch_lightning.trainer.tra
                                      iner.Trainer.callbacks`. Default: ``True``.
                                      (default is 'yes')
    <BLANKLINE>
      enable_model_summary            Whether to enable model summarization by
                                      default. Default: ``True``. (default is
                                      'yes')
    <BLANKLINE>
      enable_progress_bar             Whether to enable to progress bar by
                                      default. Default: ``False``. (default is
                                      'yes')
    <BLANKLINE>
      fast_dev_run                    Runs n if set to ``n`` (int) else 1 if set
                                      to ``True`` batch(es) of train, val and test
                                      to find any bugs (ie: a sort of unit test).
                                      Default: ``False``. (default is 'no')
    <BLANKLINE>
      flush_logs_every_n_steps        How often to flush logs to disk (defaults to
                                      every 100 steps). .. deprecated:: v1.5
                                      ``flush_logs_every_n_steps`` has been
                                      deprecated in v1.5 and will be removed in
                                      v1.7. Please configure flushing directly in
                                      the logger instead.
    <BLANKLINE>
      gpus                            Number of GPUs to train on (int) or which
                                      GPUs to train on (list or str) applied per
                                      node Default: ``None``.
    <BLANKLINE>
      gradient_clip_algorithm         The gradient clipping algorithm to use. Pass
                                      ``gradient_clip_algorithm="value"`` to clip
                                      by value, and
                                      ``gradient_clip_algorithm="norm"`` to clip
                                      by norm. By default it will be set to
                                      ``"norm"``.
    <BLANKLINE>
      gradient_clip_val               The value at which to clip gradients.
                                      Passing ``gradient_clip_val=None`` disables
                                      gradient clipping. If using Automatic Mixed
                                      Precision (AMP), the gradients will be
                                      unscaled before. Default: ``None``.
    <BLANKLINE>
      ipus                            How many IPUs to train on. Default:
                                      ``None``.
    <BLANKLINE>
      limit_predict_batches           How much of prediction dataset to check
                                      (float = fraction, int = num_batches).
                                      Default: ``1.0``.
    <BLANKLINE>
      limit_test_batches              How much of test dataset to check (float =
                                      fraction, int = num_batches). Default:
                                      ``1.0``.
    <BLANKLINE>
      limit_train_batches             How much of training dataset to check (float
                                      = fraction, int = num_batches). Default:
                                      ``1.0``.
    <BLANKLINE>
      limit_val_batches               How much of validation dataset to check
                                      (float = fraction, int = num_batches).
                                      Default: ``1.0``.
    <BLANKLINE>
      log_every_n_steps               How often to log within steps. Default:
                                      ``50``. (default is 50)
    <BLANKLINE>
      log_gpu_memory                  None, 'min_max', 'all'. Might slow
                                      performance. .. deprecated:: v1.5 Deprecated
                                      in v1.5.0 and will be removed in v1.7.0
                                      Please use the ``DeviceStatsMonitor``
                                      callback directly instead.
    <BLANKLINE>
      logger                          Logger (or iterable collection of loggers)
                                      for experiment tracking. A ``True`` value
                                      uses the default ``TensorBoardLogger``.
                                      ``False`` will disable logging. If multiple
                                      loggers are provided and the `save_dir`
                                      property of that logger is not set, local
                                      files (checkpoints, profiler traces, etc.)
                                      are saved in ``default_root_dir`` rather
                                      than in the ``log_dir`` of any of the
                                      individual loggers. Default: ``True``.
                                      (default is 'yes')
    <BLANKLINE>
      lr                              Learning rate for the Adam optimizer
                                      (default is 0.001)
    <BLANKLINE>
      max_epochs                      Stop training once this number of epochs is
                                      reached. Disabled by default (None). If both
                                      max_epochs and max_steps are not specified,
                                      defaults to ``max_epochs = 1000``. To enable
                                      infinite training, set ``max_epochs = -1``.
    <BLANKLINE>
      max_steps                       Stop training after this number of steps.
                                      Disabled by default (-1). If ``max_steps =
                                      -1`` and ``max_epochs = None``, will default
                                      to ``max_epochs = 1000``. To enable infinite
                                      training, set ``max_epochs`` to ``-1``.
                                      (default is -1)
    <BLANKLINE>
      max_time                        Stop training after this amount of time has
                                      passed. Disabled by default (``None``). The
                                      time duration can be specified in the format
                                      DD:HH:MM:SS (days, hours, minutes seconds),
                                      as a :class:`datetime.timedelta`, or a
                                      dictionary with keys that will be passed to
                                      :class:`datetime.timedelta`.
    <BLANKLINE>
      min_epochs                      Force training for at least these many
                                      epochs. Disabled by default (None).
    <BLANKLINE>
      min_steps                       Force training for at least these number of
                                      steps. Disabled by default (``None``).
    <BLANKLINE>
      move_metrics_to_cpu             Whether to force internal logged metrics to
                                      be moved to cpu. This can save some gpu
                                      memory, but can make training slower. Use
                                      with attention. Default: ``False``. (default
                                      is 'no')
    <BLANKLINE>
      multiple_trainloader_mode       How to loop over the datasets when there are
                                      multiple train loaders. In 'max_size_cycle'
                                      mode, the trainer ends one epoch when the
                                      largest dataset is traversed, and smaller
                                      datasets reload when running out of their
                                      data. In 'min_size' mode, all the datasets
                                      reload when reaching the minimum length of
                                      datasets. Default: ``"max_size_cycle"``.
                                      (default is max_size_cycle)
    <BLANKLINE>
      num_nodes                       Number of GPU nodes for distributed
                                      training. Default: ``1``. (default is 1)
    <BLANKLINE>
      num_processes                   Number of processes for distributed training
                                      with ``accelerator="cpu"``. Default: ``1``.
    <BLANKLINE>
      num_sanity_val_steps            Sanity check runs n validation batches
                                      before starting the training routine. Set it
                                      to `-1` to run all batches in all validation
                                      dataloaders. Default: ``2``. (default is 2)
    <BLANKLINE>
      overfit_batches                 Overfit a fraction of training data (float)
                                      or a set number of batches (int). Default:
                                      ``0.0``. (default is 0.0)
    <BLANKLINE>
      plugins                         Plugins allow modification of core behavior
                                      like ddp and amp, and enable custom
                                      lightning plugins. Default: ``None``.
    <BLANKLINE>
      precision                       Double precision (64), full precision (32),
                                      half precision (16) or bfloat16 precision
                                      (bf16). Can be used on CPU, GPU, TPUs, HPUs
                                      or IPUs. Default: ``32``. (default is 32)
    <BLANKLINE>
                                      Choices:  16, 32, 64
    <BLANKLINE>
      prepare_data_per_node           If True, each LOCAL_RANK=0 will call prepare
                                      data. Otherwise only NODE_RANK=0,
                                      LOCAL_RANK=0 will prepare data ..
                                      deprecated:: v1.5 Deprecated in v1.5.0 and
                                      will be removed in v1.7.0 Please set
                                      ``prepare_data_per_node`` in
                                      ``LightningDataModule`` and/or
                                      ``LightningModule`` directly instead.
    <BLANKLINE>
      process_position                Orders the progress bar when running
                                      multiple models on same machine. ..
                                      deprecated:: v1.5 ``process_position`` has
                                      been deprecated in v1.5 and will be removed
                                      in v1.7. Please pass :class:`~pytorch_lightn
                                      ing.callbacks.progress.TQDMProgressBar` with
                                      ``process_position`` directly to the
                                      Trainer's ``callbacks`` argument instead.
                                      (default is 0)
    <BLANKLINE>
      profiler                        To profile individual steps during training
                                      and assist in identifying bottlenecks.
                                      Default: ``None``.
    <BLANKLINE>
      progress_bar_refresh_rate       How often to refresh progress bar (in
                                      steps). Value ``0`` disables progress bar.
                                      Ignored when a custom progress bar is passed
                                      to :paramref:`~Trainer.callbacks`. Default:
                                      None, means a suitable value will be chosen
                                      based on the environment (terminal, Google
                                      COLAB, etc.). .. deprecated:: v1.5
                                      ``progress_bar_refresh_rate`` has been
                                      deprecated in v1.5 and will be removed in
                                      v1.7. Please pass :class:`~pytorch_lightning
                                      .callbacks.progress.TQDMProgressBar` with
                                      ``refresh_rate`` directly to the Trainer's
                                      ``callbacks`` argument instead. To disable
                                      the progress bar, pass ``enable_progress_bar
                                      = False`` to the Trainer.
    <BLANKLINE>
      reload_dataloaders_every_n_epochs
                                      Set to a non-negative integer to reload
                                      dataloaders every n epochs. Default: ``0``.
                                      (default is 0)
    <BLANKLINE>
      replace_sampler_ddp             Explicitly enables or disables sampler
                                      replacement. If not specified this will
                                      toggled automatically when DDP is used. By
                                      default it will add ``shuffle=True`` for
                                      train sampler and ``shuffle=False`` for
                                      val/test sampler. If you want to customize
                                      it, you can set
                                      ``replace_sampler_ddp=False`` and add your
                                      own distributed sampler. (default is 'yes')
    <BLANKLINE>
      resume_from_checkpoint          Path/URL of the checkpoint from which
                                      training is resumed. If there is no
                                      checkpoint file at the path, an exception is
                                      raised. If resuming from mid-epoch
                                      checkpoint, training will start from the
                                      beginning of the next epoch. .. deprecated::
                                      v1.5 ``resume_from_checkpoint`` is
                                      deprecated in v1.5 and will be removed in
                                      v2.0. Please pass the path to
                                      ``Trainer.fit(..., ckpt_path=...)`` instead.
    <BLANKLINE>
      stochastic_weight_avg           Whether to use `Stochastic Weight Averaging
                                      (SWA)
                                      <https://pytorch.org/blog/pytorch-1.6-now-
                                      includes-stochastic-weight-averaging/>`_.
                                      Default: ``False``. .. deprecated:: v1.5
                                      ``stochastic_weight_avg`` has been
                                      deprecated in v1.5 and will be removed in
                                      v1.7. Please pass :class:`~pytorch_lightning
                                      .callbacks.stochastic_weight_avg.StochasticW
                                      eightAveraging` directly to the Trainer's
                                      ``callbacks`` argument instead. (default is
                                      'no')
    <BLANKLINE>
      strategy                        Supports different training strategies with
                                      aliases as well custom strategies. Default:
                                      ``None``.
    <BLANKLINE>
      sync_batchnorm                  Synchronize batch norm layers between
                                      process groups/whole world. Default:
                                      ``False``. (default is 'no')
    <BLANKLINE>
      terminate_on_nan                If set to True, will terminate training (by
                                      raising a `ValueError`) at the end of each
                                      training batch, if any of the parameters or
                                      the loss are NaN or +/-inf. .. deprecated::
                                      v1.5 Trainer argument ``terminate_on_nan``
                                      was deprecated in v1.5 and will be removed
                                      in 1.7. Please use ``detect_anomaly``
                                      instead.
    <BLANKLINE>
      tpu_cores                       How many TPU cores to train on (1 or 8) /
                                      Single TPU to train on (1) Default:
                                      ``None``.
    <BLANKLINE>
      track_grad_norm                 -1 no tracking. Otherwise tracks that
                                      p-norm. May be set to 'inf' infinity-norm.
                                      If using Automatic Mixed Precision (AMP),
                                      the gradients will be unscaled before
                                      logging them. Default: ``-1``. (default is
                                      -1)
    <BLANKLINE>
      val_check_interval              How often to check the validation set. Pass
                                      a ``float`` in the range [0.0, 1.0] to check
                                      after a fraction of the training epoch. Pass
                                      an ``int`` to check after a fixed number of
                                      training batches. Default: ``1.0``.
    <BLANKLINE>
      weights_save_path               Where to save weights if specified. Will
                                      override default_root_dir for checkpoints
                                      only. Use this if for whatever reason you
                                      need the checkpoints stored in a different
                                      place than the logs written in
                                      `default_root_dir`. Can be remote file paths
                                      such as `s3://mybucket/path` or
                                      'hdfs://path/' Defaults to
                                      `default_root_dir`. .. deprecated:: v1.6
                                      ``weights_save_path`` has been deprecated in
                                      v1.6 and will be removed in v1.8. Please
                                      pass ``dirpath`` directly to the :class:`~py
                                      torch_lightning.callbacks.model_checkpoint.M
                                      odelCheckpoint` callback.
    <BLANKLINE>
      weights_summary                 Prints a summary of the weights when
                                      training begins. .. deprecated:: v1.5
                                      ``weights_summary`` has been deprecated in
                                      v1.5 and will be removed in v1.7. To disable
                                      the summary, pass ``enable_model_summary =
                                      False`` to the Trainer. To customize the
                                      summary, pass :class:`~pytorch_lightning.cal
                                      lbacks.model_summary.ModelSummary` directly
                                      to the Trainer's ``callbacks`` argument.
                                      (default is top)
    <exit 0>

Print the command.

    >>> run("guild run mnist.py --print-cmd | tr ' ' '\n'",
    ...     env={"NO_IMPORT_FLAGS_CACHE": "1"})  # doctest: +REPORT_UDIFF -PY35 -PY2 -PY36
    ???
    -um
    guild.op_main
    mnist
    --amp_backend
    native
    --auto_lr_find
    no
    --auto_scale_batch_size
    no
    --auto_select_gpus
    no
    --check_val_every_n_epoch
    1
    --detect_anomaly
    no
    --enable_checkpointing
    yes
    --enable_model_summary
    yes
    --enable_progress_bar
    yes
    --fast_dev_run
    no
    --log_every_n_steps
    50
    --logger
    yes
    --lr
    0.001
    --max_steps
    -1
    --move_metrics_to_cpu
    no
    --multiple_trainloader_mode
    max_size_cycle
    --num_nodes
    1
    --num_sanity_val_steps
    2
    --overfit_batches
    0.0
    --precision
    32
    --process_position
    0
    --reload_dataloaders_every_n_epochs
    0
    --replace_sampler_ddp
    yes
    --stochastic_weight_avg
    no
    --sync_batchnorm
    no
    --track_grad_norm
    -1.0
    --weights_summary
    top
    <exit 0>

Print the command using the `train` operation, which imports all flags.

    >>> run("guild run train --print-cmd | tr ' ' '\n'",
    ...     env={"NO_IMPORT_FLAGS_CACHE": "1"}) # doctest: +REPORT_UDIFF -PY35 -PY2 -PY36
    ???
    -um
    guild.op_main
    mnist
    --
    --amp_backend
    native
    --auto_lr_find
    no
    --auto_scale_batch_size
    no
    --auto_select_gpus
    no
    --check_val_every_n_epoch
    1
    --detect_anomaly
    no
    --enable_checkpointing
    yes
    --enable_model_summary
    yes
    --enable_progress_bar
    yes
    --fast_dev_run
    no
    --log_every_n_steps
    50
    --logger
    yes
    --lr
    0.001
    --max_steps
    -1
    --move_metrics_to_cpu
    no
    --multiple_trainloader_mode
    max_size_cycle
    --num_nodes
    1
    --num_sanity_val_steps
    2
    --overfit_batches
    0.0
    --precision
    32
    --process_position
    0
    --reload_dataloaders_every_n_epochs
    0
    --replace_sampler_ddp
    yes
    --stochastic_weight_avg
    no
    --sync_batchnorm
    no
    --track_grad_norm
    -1.0
    --weights_summary
    top
    <exit 0>
