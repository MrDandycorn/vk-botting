.. currentmodule:: vk_botting

.. _vk_api_commands:

Commands
==========

One of the most appealing aspect of the command extension is how easy it is to define commands and
how you can arbitrarily nest groups and commands to have a rich sub-command system.

Commands are defined by attaching it to a regular Python function. The command is then invoked by the user using a similar
signature to the Python function.

For example, in the given command definition:

.. code-block:: python3

    @bot.command()
    async def foo(ctx, arg):
        await ctx.send(arg)

With the following prefix (``$``), it would be invoked by the user via:

.. code-block:: none

    $foo abc

A command must always have at least one parameter, ``ctx``, which is the :class:`.Context` as the first one.

There are two ways of registering a command. The first one is by using :meth:`.Bot.command` decorator,
as seen in the example above. The second is using the :func:`~ext.commands.command` decorator followed by
:meth:`.Bot.add_command` on the instance.

Essentially, these two are equivalent: ::

    import vk_botting

    bot = vk_botting.Bot(command_prefix='$')

    @bot.command()
    async def test(ctx):
        pass

    # or:

    @vk_botting.command()
    async def test(ctx):
        pass

    bot.add_command(test)

Since the :meth:`.Bot.command` decorator is shorter and easier to comprehend, it will be the one used throughout the
documentation here.

Any parameter that is accepted by the :class:`.Command` constructor can be passed into the decorator. For example, to change
the name to something other than the function would be as simple as doing this:

.. code-block:: python3

    @bot.command(name='list')
    async def _list(ctx, arg):
        pass

Parameters
------------

Since we define commands by making Python functions, we also define the argument passing behaviour by the function
parameters.

Certain parameter types do different things in the user side and most forms of parameter types are supported.

Positional
++++++++++++

The most basic form of parameter passing is the positional parameter. This is where we pass a parameter as-is:

.. code-block:: python3

    @bot.command()
    async def test(ctx, arg):
        await ctx.send(arg)


On the bot using side, you can provide positional arguments by just passing a regular string:

Since positional arguments are just regular Python arguments, you can have as many as you want:

.. code-block:: python3

    @bot.command()
    async def test(ctx, arg1, arg2):
        await ctx.send('You passed {} and {}'.format(arg1, arg2))

Variable
++++++++++

Sometimes you want users to pass in an undetermined number of parameters. The library supports this
similar to how variable list parameters are done in Python:

.. code-block:: python3

    @bot.command()
    async def test(ctx, *args):
        await ctx.send('{} arguments: {}'.format(len(args), ', '.join(args)))

This allows our user to accept either one or many arguments as they please.

Do note that similar to the Python function behaviour, a user can technically pass no arguments
at all.

Since the ``args`` variable is a :class:`py:tuple`,
you can do anything you would usually do with one.

Keyword-Only Arguments
++++++++++++++++++++++++

When you want to handle parsing of the argument yourself or do not feel like you want to wrap multi-word user input into
quotes, you can ask the library to give you the rest as a single argument. We do this by using a **keyword-only argument**,
seen below:

.. code-block:: python3

    @bot.command()
    async def test(ctx, *, arg):
        await ctx.send(arg)

.. warning::

    You can only have one keyword-only argument due to parsing ambiguities.

By default, the keyword-only arguments are stripped of white space to make it easier to work with. This behaviour can be
toggled by the :attr:`.Command.rest_is_raw` argument in the decorator.

.. _vk_api_context:

Invocation Context
-------------------

As seen earlier, every command must take at least a single parameter, called the :class:`context.Context`.

This parameter gives you access to something called the "invocation context". Essentially all the information you need to
know how the command was executed. It contains a lot of useful information:

- :attr:`.Context.from_id` to fetch the id of message author.
- :attr:`.Context.peer_id` to fetch id of conversation.
- :meth:`.Context.get_user` to fetch the :class:`User` that called the command.
- :meth:`.Context.send` to send a message to the conversation the command was used in.

The context implements the :class:`abstract.Messageable` interface, so anything you can do on a :class:`abstract.Messageable` you
can do on the :class:`context.Context`.

Converters
------------

Adding bot arguments with function parameters is only the first step in defining your bot's command interface. To actually
make use of the arguments, we usually want to convert the data into a target type. We call these
Converters.

Converters come in a few flavours:

- A regular callable object that takes an argument as a sole parameter and returns a different type.

    - These range from your own function, to something like :class:`bool` or :class:`int`.

- A custom class that inherits from :class:`conversions.Converter`.

Basic Converters
++++++++++++++++++

At its core, a basic converter is a callable that takes in an argument and turns it into something else.

For example, if we wanted to add two numbers together, we could request that they are turned into integers
for us by specifying the converter:

.. code-block:: python3

    @bot.command()
    async def add(ctx, a: int, b: int):
        await ctx.send(a + b)

We specify converters by using something called a **function annotation**. This is a Python 3 exclusive feature that was
introduced in :pep:`3107`.

This works with any callable, such as a function that would convert a string to all upper-case:

.. code-block:: python3

    def to_upper(argument):
        return argument.upper()

    @bot.command()
    async def up(ctx, *, content: to_upper):
        await ctx.send(content)

bool
^^^^^^

Unlike the other basic converters, the :class:`bool` converter is treated slightly different. Instead of casting directly to the :class:`bool` type, which would result in any non-empty argument returning ``True``, it instead evaluates the argument as ``True`` or ``False`` based on its given content:

.. code-block:: python3

    if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on', 'да', 'включить', 'правда'):
        return True
    elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off', 'нет', 'выключить', 'ложь'):
        return False

.. _vk_api_adv_converters:

Advanced Converters
+++++++++++++++++++++

Sometimes a basic converter doesn't have enough information that we need. For example, sometimes we want to get some
information from the :class:`Message` that called the command or we want to do some asynchronous processing.

For this, the library provides the :class:`conversions.Converter` interface. This allows you to have access to the
:class:`.Context` and have the callable be asynchronous. Defining a custom converter using this interface requires
overriding a single method, :meth:`.Converter.convert`.

An example converter:

.. code-block:: python3

    import random

    class Slapper(commands.Converter):
        async def convert(self, ctx, argument):
            to_slap = random.choice(['foo', 'bar'])
            return '{0.from_id} slapped {1} because *{2}*'.format(ctx, to_slap, argument)

    @bot.command()
    async def slap(ctx, *, reason: Slapper):
        await ctx.send(reason)

The converter provided can either be constructed or not. Essentially these two are equivalent:

.. code-block:: python3

    @bot.command()
    async def slap(ctx, *, reason: Slapper):
        await ctx.send(reason)

    # is the same as...

    @bot.command()
    async def slap(ctx, *, reason: Slapper()):
        await ctx.send(reason)

Having the possibility of the converter be constructed allows you to set up some state in the converter's ``__init__`` for
fine tuning the converter.

If a converter fails to convert an argument to its designated target type, the :exc:`.BadArgument` exception must be
raised.


.. _vk_api_error_handler:

Error Handling
----------------

When our commands fail to parse we will, by default, receive a noisy error in ``stderr`` of our console that tells us
that an error has happened and has been silently ignored.

In order to handle our errors, we must use something called an error handler. There is a global error handler, called
:func:`on_command_error` which works like any other event in the :ref:`vk_api_events`. This global error handler is
called for every error reached.

Most of the time however, we want to handle an error local to the command itself. Luckily, commands come with local error
handlers that allow us to do just that. First we decorate an error handler function with :meth:`.Command.error`:

.. code-block:: python3

    @bot.command()
    async def info(ctx):
        """Tells you some info about the author."""
        user = await ctx.get_user()
        fmt = '{0.first_name} was last seen on {0.last_seen}.'
        await ctx.send(fmt.format(user))

    @info.error
    async def info_error(ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('Why is it here. It takes no arguments :thonk:')

The first parameter of the error handler is the :class:`.Context` while the second one is an exception that is derived from
:exc:`exceptions.CommandError`. A list of errors is found in the :ref:`vk_api_errors` page of the documentation.

Checks
-------

There are cases when we don't want a user to use our commands. They don't have permissions to do so or maybe we blocked
them from using our bot earlier. The commands extension comes with full support for these things in a concept called a
:ref:`vk_api_checks`.

A check is a basic predicate that can take in a :class:`.Context` as its sole parameter. Within it, you have the following
options:

- Return ``True`` to signal that the person can run the command.
- Return ``False`` to signal that the person cannot run the command.
- Raise a :exc:`exceptions.CommandError` derived exception to signal the person cannot run the command.

    - This allows you to have custom error messages for you to handle in the
      :ref:`error handlers <vk_api_error_handler>`.

To register a check for a command, we would have two ways of doing so. The first is using the :meth:`limiters.check`
decorator. For example:

.. code-block:: python3

    async def is_owner(ctx):
        return ctx.author == 1234567890

    @bot.command(name='eval')
    @limiters.check(is_owner)
    async def _eval(ctx, *, code):
        """A bad example of an eval command"""
        await ctx.send(eval(code))

This would only evaluate the command if the function ``is_owner`` returns ``True``. Sometimes we re-use a check often and
want to split it into its own decorator. To do that we can just add another level of depth:

.. code-block:: python3

    def is_owner():
        async def predicate(ctx):
            return ctx.author == 1234567890
        return limiters.check(predicate)

    @bot.command(name='eval')
    @is_owner()
    async def _eval(ctx, *, code):
        """A bad example of an eval command"""
        await ctx.send(eval(code))


Library actually provides a premade check to check if user is in given list (:func:`limitest.in_user_list`):

.. code-block:: python3

    @bot.command(name='eval')
    @limiters.in_user.list(1234567890)
    async def _eval(ctx, *, code):
        """A bad example of an eval command"""
        await ctx.send(eval(code))

When multiple checks are specified, **all** of them must be ``True``:

.. code-block:: python3

    def in_conversation(guild_id):
        async def predicate(ctx):
            return ctx.peer_id != ctx.from_id
        return commands.check(predicate)

    @bot.command()
    @limiters.in_user.list(1234567890)
    @in_conversation()
    async def secretdata(ctx):
        """super secret stuff"""
        await ctx.send('secret stuff')

If any of those checks fail in the example above, then the command will not be run.

When an error happens, the error is propagated to the :ref:`error handlers <vk_api_error_handler>`. If you do not
raise a custom :exc:`exceptions.CommandError` derived exception, then it will get wrapped up into a
:exc:`exceptions.CheckFailure` exception as so:

.. code-block:: python3

    @bot.command()
    @limiters.in_user.list(1234567890)
    @in_conversation()
    async def secretdata(ctx):
        """super secret stuff"""
        await ctx.send('secret stuff')

    @secretdata.error
    async def secretdata_error(ctx, error):
        if isinstance(error, exceptions.CheckFailure):
            await ctx.send('nothing to see here comrade.')

Global Checks
++++++++++++++

Sometimes we want to apply a check to **every** command, not just certain commands. The library supports this as well
using the global check concept.

Global checks work similarly to regular checks except they are registered with the :func:`.Bot.check` decorator.

For example, to block all DMs we could do the following:

.. code-block:: python3

    @bot.check
    async def globally_block_dms(ctx):
        return ctx.from_id != ctx.peer_id

.. warning::

    Be careful on how you write your global checks, as it could also lock you out of your own bot.
