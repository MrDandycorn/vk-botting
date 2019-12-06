.. currentmodule:: vk-botting

.. _quickstart:

Quickstart
============

This page gives a brief introduction to the library. It assumes you have the library installed,
if you don't check the :ref:`installing` portion.

A Minimal Bot
---------------

Let's make a bot that replies to a specific message and walk you through it.

It looks something like this:

.. code-block:: python3

    import vk_botting

    bot = vk_botting.Bot('your-prefix-here')


    @bot.listen()
    async def on_ready():
        print(f'Logged in as {bot.group.name}')


    @bot.listen()
    async def on_message_new(message):
        if message.text.startswith('Hello'):
            await message.send('Hello!')


    bot.run('your-token-here')

Let's name this file ``example_bot.py``.

There's a lot going on here, so let's walk you through it step by step.

1. The first line just imports the library, if this raises a `ModuleNotFoundError` or `ImportError`
   then head on over to :ref:`installing` section to properly install.
2. Next, we create an instance of a :class:`Bot`. This bot is our connection to VK.
3. We then use the :meth:`Bot.listen()` decorator to register an event. This library has many events.
   Since this library is asynchronous, we do things in a "callback" style manner.

   A callback is essentially a function that is called when something happens. In our case,
   the :func:`on_ready` event is called when the bot has finished logging in and setting things
   up and the :func:`on_message_new` event is called when the bot has received a message.
4. Afterwards, we check if the :class:`Message.text` starts with ``'$hello'``. If it is,
   then we reply to the sender with ``'Hello!'``.
5. Finally, we run the bot with our login token. If you need help getting your token or creating a bot,
   look in the :ref:`vk-intro` section.


Now that we've made a bot, we have to *run* the bot. Luckily, this is simple since this is just a
Python script, we can run it directly.

On Windows:

.. code-block:: shell

    $ py -3 example_bot.py

On other systems:

.. code-block:: shell

    $ python3 example_bot.py

Now you can try playing around with your basic bot.


Commands usage
---------------

vk-botting package has a lot of possibilities for creating commands easily.

Look at this example:

.. code-block:: python3

    import vk_botting

    bot = vk_botting.Bot('your-prefix-here')


    @bot.listen()
    async def on_ready():
        print(f'Logged in as {bot.group.name}')


    @bot.listen()
    async def on_message_new(message):
        if message.text.startswith('Hello'):
            await message.send('Hello!')


    @bot.command(name='greet')
    async def greet(context):
        await context.reply('Greetings!')


    bot.run('your-token-here')

As you can see, this is a slightly modified version of previous bot.

The difference is the :func:`bot.command` part

The commands are automatically processed messages. You may have noticed that we
used a prefix when creating our bot, and the commands are what this prefix
is needed for.

They are created using :func:`Bot.command` decorator, that can take several
arguments, for example :attr:`name` we used here. By default it will be
function name, so we didn't really need it here, but it is just more
human-readable this way

So, for example, let's say your prefix of choice was ``'!'``. It can really be
anything, but we will talk about that later.

So, now when user sends ``!greet`` to the bot, the bot will reply with
``Greetings!``

:attr:`context` here is the instance of the :class:`Context` class , which is automatically
put into every command's first argument, so be aware of it.

:class:`Context` has all the information you need to process the command
You can find more information in the Context class reference

Commands can also take arguments, as shown here

.. code-block:: python3

    @bot.command(name='greet')
    async def greet(context, name):
        await context.reply(f'Greetings, {name}!')


Now user can call command like ``!greet Santa`` and the bot will reply with
``Greetings, Santa``. Arguments taken are positional, and separated with space
by default, so if user will call ``!greet Santa Claus`` bot will still reply with
just ``Greetings, Santa``.

If you want to get all of the text user sent after certain argument (or
even after the command call), you can set up arguments like this

.. code-block:: python3

    @bot.command(name='greet')
    async def greet(context, *, name):
        await context.reply(f'Greetings, {name}!')

Now bot will put everything after the command call into :attr:`name` variable
so now you can greet someone with longer name
