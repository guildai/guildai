# NetworkX

    >>> import networkx as nx

## DAG dependencies

This example is derrived from:

https://ipython.org/ipython-doc/3/parallel/dag_dependencies.html

Consider this dependency graph:

    >>> g = nx.OrderedDiGraph()
    >>> g.add_edge(0, 1)
    >>> g.add_edge(0, 2)
    >>> g.add_edge(1, 3)
    >>> g.add_edge(2, 3)
    >>> g.add_edge(1, 4)

In this implementation, dependencies are read "RHS depends on
LHS". So, "1 depends on 0", "2 depends on 0", and so on.

Using `topological_sort` we can list the nodes an order they might be
executed in that ensures that required nodes are run first:

    >>> for node in nx.topological_sort(g):
    ...    print(node)
    0
    2
    1
    4
    3

We can further use threads to simulate tasks that run concurrently
where possible. In our sample graph, nodes 1 and 2 can run
concurrently, which node 3 waits on both nodes 1 and 2 and node 4
waits on node 1.

To illustrate, we'll use a thread for each task that ensures node
dependencies are completed before proceeding.

    >>> import threading, time, random

    >>> class Task(threading.Thread):
    ...
    ...   def __init__(self, node, deps):
    ...     super(Task, self).__init__()
    ...     self.node = node
    ...     self.deps = deps
    ...     self.started = None
    ...
    ...   def run(self):
    ...     for dep in self.deps:
    ...       dep.join()
    ...     self.started = time.time()
    ...     time.sleep(random.random() * 0.2)

Create and strart our tasks:

    >>> tasks = {}
    >>> for node in nx.topological_sort(g):
    ...   deps = [tasks[dep] for dep in g.predecessors(node)]
    ...   task = Task(node, deps)
    ...   tasks[node] = task
    ...   task.start()

Wait for the tasks to finish:

    >>> for task in tasks.values():
    ...   task.join()

We can assert the relative `started` attribute for each task.

Task 0 started first:

    >>> (tasks[0].started < tasks[1].started and
    ...  tasks[0].started < tasks[2].started and
    ...  tasks[0].started < tasks[3].started and
    ...  tasks[0].started < tasks[4].started)
    True

Task 3 started after 1 and 2:

    >>> (tasks[3].started > tasks[1].started and
    ...  tasks[3].started > tasks[2].started)
    True

Task 4 started after task 1:

    >>> tasks[4].started > tasks[1].started
    True
