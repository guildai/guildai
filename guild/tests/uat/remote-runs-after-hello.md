# Runs after remote hello ops

    >>> run("guild runs list --remote guild-uat")
    [1:...]  gpkg.hello/hello-op    ...  completed  op=...
    [2:...]  gpkg.hello/hello-file  ...  completed  file=hello.txt
    [3:...]  gpkg.hello/hello       ...  completed  msg='Hello Guild!'
    [4:...]  gpkg.hello/hello-op    ...  completed  op=...
    [5:...]  gpkg.hello/hello-file  ...  completed  file=hello-2.txt
    [6:...]  gpkg.hello/hello       ...  completed  msg='Hello Guild!'
    [7:...]  hello/hello:from-file  ...  completed  h2 file=msg.txt
    [8:...]  hello/hello:from-flag  ...  completed  message='Howdy Guild!'
    [9:...]  hello/hello:default    ...  completed  h1
    <exit 0>
