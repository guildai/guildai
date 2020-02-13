# Guild Example: `features`

This is an experimental example to show how one might use flags to
enable features for testing.

- [test.py](test.py) - Test script

Use:

```
$ guild run test.py a=[0,1] b=[0,1] c=[0,1] --print-trials
#  a  b  c
1  0  0  0
2  0  0  1
3  0  1  0
4  0  1  1
5  1  0  0
6  1  0  1
7  1  1  0
8  1  1  1
```
