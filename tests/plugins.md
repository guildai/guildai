# Plugins

Plugin support is providedy by `guild.plugin`:

    >>> import guild.plugin

We need to explicitly initialize plugins by calling `init_plugins`:

    >>> guild.plugin.init_plugins()

## Enumerating plugins

Use `iter_plugins` to iterate through the list of available plugins:

    >>> sorted(guild.plugin.iter_plugins())
    [('gpu', <guild.plugins.gpu.GPUPlugin object ...>),
     ('keras', <guild.plugins.keras.KerasPlugin object ...>)]

## Plugin instances

You can get the plugin instance using `for_name`:

    >>> guild.plugin.for_name("gpu")
    <guild.plugins.gpu.GPUPlugin object ...>

There is only ever one plugin instance for a given name:

    >>> guild.plugin.for_name("gpu") is guild.plugin.for_name("gpu")
    True

## Plugin helpers

### Listen method

Plugins routinely patch the environment to perform additional
actions. One such patch is to listen for method calls on various
classes. The `listen_method` function can be used to reveive
notification when a method is called.

Let's create a class with a method that prints a message:

    >>> class Hello(object):
    ...   def say(self, msg):
    ...     print(msg)

Let's patch `say`:

    >>> def wrap_say(say, msg):
    ...   say("I've wrapped '%s'" % msg)
    >>> guild.plugin.listen_method(Hello.say, wrap_say)

When we call `hello` on an object:

    >>> hello = Hello()
    >>> hello.say("Hello Guild!")
    I've wrapped 'Hello Guild!'
    Hello Guild!

The arg `say` is the original wrapped function, which can be called by
the wrapping function.

We can wrap a method multiple times. In this case we'll wrap using an
instance method:

    >>> class Wrapper(object):
    ...   def __init__(self, method):
    ...     guild.plugin.listen_method(method, self.wrap_say)
    ...
    ...   def wrap_say(self, say, msg):
    ...     say("I've also wrapped '%s'" % msg)

    >>> wrapper = Wrapper(Hello.say)
    >>> hello.say("Hello again!")
    I've wrapped 'Hello again!'
    I've also wrapped 'Hello again!'
    Hello again!

A wrapper can prevent the call to the wrapped function by returning
False.

    >>> def wrap_and_prevent_original(say, msg):
    ...   say("I've wrapped '%s' and prevented the original call!" % msg)
    ...   return False
    >>> guild.plugin.listen_method(Hello.say, wrap_and_prevent_original)
    >>> hello.say("Hello once more!")
    I've wrapped 'Hello once more!'
    I've also wrapped 'Hello once more!'
    I've wrapped 'Hello once more!' and prevented the original call!

Finally, we can remove all listeners on a method:

    >>> guild.plugin.remove_listeners(hello.say)
    >>> hello.say("Hello, without listeners!")
    Hello, without listeners!
