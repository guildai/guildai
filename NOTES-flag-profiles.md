# Flag profiles

We need to support a mechanism for defining sets of related flags. For
the sake of this discussion, we refer to these sets as *flag
profiles*.

A flag profile defines a set of flag values. For example:

```
learning-rate: 0.01
q: 10
N: 100
```

Where is this profile defined?

Logical places:

- In the Guild file
- In an external file

In the Guild file, example:

``` yaml
- model: m
  operations:
    train:
      flags:
        learning-rate: null
        q: null
        N: null

- profile: 1
  learning-rate: 0.01
  q: 10
  N: 100

- profile: 2
  learning-rate: 0.01
  q: 100
  N: 10000
```

Alernatively:

``` yaml
- model: m
  operations:
    train:
      flags:
        learning-rate:
          description: Learning rate
          default: [0.01]
        q:
          description: Some param q
          default: [10, 100]
        N:
          description: Some value N
          default: [100, 10000]
```
