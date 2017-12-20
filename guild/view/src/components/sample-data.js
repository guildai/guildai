export var SampleRuns = [
  {
    shortId: 'e61e0ba2',
    operation: './slim-resnet-v2-152:fine-tune',
    opModel: 'slim-resnet-v2-152',
    opName: 'fine-tune',
    started: '2017-12-06 11:51:15',
    stopped: '2017-12-06 11:51:18',
    status: 'error',
    exitStatus: 1,
    command: '/usr/bin/python -u /home/garrett/SCM/guild/guild/scripts/run slim_op train_image_classifier --model_name resnet_v2_50 --train_dir . --dataset_split_name train --dataset_dir data --checkpoint_path resnet_v2_50.ckpt --checkpoint_exclude_scopes resnet_v2_50/logits --trainable_scopes resnet_v2_50/logits --batch_size 4 --dataset_name flowers --learning_rate 0.01 --learning_rate_decay_type exponential --log_every_n_steps 100 --max_number_of_steps 1000 --optimizer rmsprop --save_interval_secs 60 --save_summaries_secs 60 --weight_decay 4e-05',
    flags: {
      'batch-size': 32,
      'dataset': 'cifar10',
      'learning-rate': 0.01,
      'learning-rate-decay-type': 'exponential',
      'log-every-n-steps': '100',
      'max-steps': 1000,
      'optimizer': 'rmsprop',
      'save-model-secs': 60,
      'save-summaries-secs': 60,
      'weight-decay': 4e-05
    },
    env: {
      'VTE_VERSION': '4205',
      'WINDOWID': '73400326',
      'WINDOWPATH': '8',
      'XAUTHORITY': '/home/garrett/.Xauthority',
      'XDG_CONFIG_DIRS': '/etc/xdg/xdg-cinnamon:/etc/xdg',
      'XDG_CURRENT_DESKTOP': 'X-Cinnamon',
      'XDG_DATA_DIRS': '/usr/share/cinnamon:/usr/share/gnome:/usr/local/share/:/usr/share/:/usr/share/mdm/',
      'XDG_RUNTIME_DIR': '/run/user/1000',
      'XDG_SEAT': 'seat0',
      'XDG_SESSION_COOKIE': '2a5d5f96ef9147c0b35535562b32d0ff-1512503364.444035-596823101',
      'XDG_SESSION_DESKTOP': 'cinnamon',
      'XDG_SESSION_ID': 'c1',
      'XDG_VTNR': '8'
    },
    deps: [
      {
        operation: 'slim.datasets/slim-flowers:prepare',
        run: '2f64285c'
      }
    ],
    files: [
      { path: 'checkpoint', type: 'Latest checkpoint marker', size: 265, icon: 'file', iconTooltip: 'File' },
      { path: 'data', type: 'Operation output link', size: null, icon: 'file-export', iconTooltip: 'Link' },
      { path: 'eval.graph', type: 'Link to resource', size: null, icon: 'file-export', iconTooltip: 'Link' },
      { path: 'events.out.tfevents.1512527577.omaha', type: 'TensorFlow event log', size: 6868836, icon: 'file', iconTooltip: 'File' },
      { path: 'graph.pbtxt', type: 'TensorFlow graph def', size: 4140777, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-0.data-00000-of-00001', type: 'TensorFlow checkpoint values', size: 94382148, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-0.index', type: 'TensorFlow checkpoint index', size: 11499, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-0.meta', type: 'TensorFlow checkpoint meta graph', size: 2005581, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-1000.data-00000-of-00001', type: 'TensorFlow checkpoint values', size: 94382148, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-1000.index', type: 'TensorFlow checkpoint index', size: 11499, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-1000.meta', type: 'TensorFlow checkpoint meta graph', size: 2005581, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-258.data-00000-of-00001', type: 'TensorFlow checkpoint values', size: 94382148, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-258.index', type: 'TensorFlow checkpoint index', size: 11499, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-258.meta', type: 'TensorFlow checkpoint meta graph', size: 2005581, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-524.data-00000-of-00001', type: 'TensorFlow checkpoint values', size: 94382148, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-524.index', type: 'TensorFlow checkpoint index', size: 11499, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-524.meta', type: 'TensorFlow checkpoint meta graph', size: 2005581, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-792.data-00000-of-00001', type: 'TensorFlow checkpoint values', size: 94382148, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-792.index', type: 'TensorFlow checkpoint index', size: 11499, icon: 'file', iconTooltip: 'File' },
      { path: 'model.ckpt-792.meta', type: 'TensorFlow checkpoint meta graph', size: 2005581, icon: 'file', iconTooltip: 'File' },
      { path: 'resnet_v2_50.ckpt', type: 'Resource link', size: null, icon: 'file-export', iconTooltip: 'Link' },
      { path: 'slim', type: 'Resource link', size: null, icon: 'file-export', iconTooltip: 'Link' },
      { path: 'train.graph', type: 'Resource link', size: null, icon: 'file-export', iconTooltip: 'Link' }
    ]
  },
  {
    shortId: '0df943ac',
    operation: './magenta-melody-rnn:compose',
    opModel: 'magenta-melody-rnn',
    opName: 'compose',
    started: '2017-12-13 13:14:31',
    stopped: '2017-12-13 13:14:34',
    status: 'completed',
    exitStatus: 0,
    command: '/usr/bin/python -u /home/garrett/SCM/guild/guild/scripts/run slim_op export_inference_graph --model_name resnet_v1_50 --dataset_dir data --output_file graph.pb --dataset_name custom',
    flags: {},
    env: {},
    deps: [],
    files: [
      { path: '2017-12-06_120417_01.mid', type: 'Audio', size: 262, icon: 'file-music', iconTooltip: 'Audio', viewer: true },
      { path: '2017-12-06_120417_02.mid', type: 'Audio', size: 153, icon: 'file-music', iconTooltip: 'Audio', viewer: true },
      { path: '2017-12-06_120417_03.mid', type: 'Audio', size: 321, icon: 'file-music', iconTooltip: 'Audio', viewer: true },
      { path: '2017-12-06_120417_04.mid', type: 'Audio', size: 344, icon: 'file-music', iconTooltip: 'Audio', viewer: true },
      { path: '2017-12-06_120417_05.mid', type: 'Audio', size: 298, icon: 'file-music', iconTooltip: 'Audio', viewer: true },
      { path: '2017-12-06_120417_06.mid', type: 'Audio', size: 183, icon: 'file-music', iconTooltip: 'Audio', viewer: true },
      { path: '2017-12-06_120417_07.mid', type: 'Audio', size: 928, icon: 'file-music', iconTooltip: 'Audio', viewer: true },
      { path: '2017-12-06_120417_08.mid', type: 'Audio', size: 372, icon: 'file-music', iconTooltip: 'Audio', viewer: true },
      { path: '2017-12-06_120417_09.mid', type: 'Audio', size: 254, icon: 'file-music', iconTooltip: 'Audio', viewer: true },
      { path: '2017-12-06_120417_10.mid', type: 'Audio', size: 211, icon: 'file-music', iconTooltip: 'Audio', viewer: true },
      { path: 'attention_rnn.mag', type: 'Resource link', size: null, icon: 'file-export', iconTooltip: 'Link' }
    ]
  },
  {
    shortId: '39d61334',
    operation: './slim-resnet-101:train',
    opModel: 'slim-resnet-101',
    opName: 'train',
    started: '2017-12-06 11:50:00',
    stopped: '2017-12-06 11:50:03',
    status: 'terminated',
    exitStatus: null,
    command: '/usr/bin/python -u /home/garrett/SCM/guild/guild/scripts/run slim_op train_image_classifier --model_name resnet_v1_101 --train_dir . --dataset_split_name train --dataset_dir data --batch_size 1 --dataset_name flowers --learning_rate 0.01 --learning_rate_decay_type exponential --log_every_n_steps 100 --max_number_of_steps 100 --optimizer rmsprop --save_interval_secs 60 --save_summaries_secs 60 --weight_decay 4e-05',
    flags: {},
    env: {},
    deps: [],
    files: [
      { path: 'arbitrary_style_transfer', type: 'Resource link', size: null, icon: 'file-export', iconTooltip: 'Link' },
      { path: 'doge.jpg', type: 'Image', size: 262, icon: 'file-image', iconTooltip: 'Image', viewer: true },
      { path: 'doge_stylized_t1_0.jpg', type: 'Image', size: 262, icon: 'file-image', iconTooltip: 'Image', viewer: true },
      { path: 't1.jpg', type: 'Image', size: 262, icon: 'file-image', iconTooltip: 'Image', viewer: true }
    ]
  }
];

export var Cwd = '~/SCM/guild-packages/slim/resnet';
