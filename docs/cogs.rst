.. currentmodule:: vk_botting

.. _vk_api_cogs:

Cogs
======

There comes a point in your bot's development when you want to organize a collection of commands, listeners, and some state into one class. Cogs allow you to do just that.

The gist:

- Each cog is a Python class that subclasses :class:`.cog.Cog`.
- Every command is marked with the :func:`~.commands.command` decorator.
- Every listener is marked with the :meth:`.cog.Cog.listener` decorator.
- Cogs are then registered with the :meth:`.Bot.add_cog` call.
- Cogs are subsequently removed with the :meth:`.Bot.remove_cog` call.

Quick Example
---------------

This example cog defines a ``Greetings`` category for your commands, with a single :ref:`command <vk_api_commands>` named ``hello`` as well as a listener to listen to an :ref:`Event <vk_api_events>`.

.. code-block:: python3

    class Greetings(cog.Cog):
        def __init__(self, bot):
            self.bot = bot
            self._last_user = None

        @cog.Cog.listener()
        async def on_chat_invite_user(self, message):
            user = await self.bot.get_user(message.action.member_id)
            await message.send('Welcome {0.mention}!'.format(user))

        @commands.command()
        async def hello(self, ctx, user_id: int = None):
            """Says hello"""
            user_id = user_id or ctx.author
            user = await self.bot.get_user(user_id)
            if self._last_user is None or self._last_user != user_id:
                await ctx.send('Hello {0.mention}~'.format(user))
            else:
                await ctx.send('Hello {0.mention}... This feels familiar.'.format(user))
            self._last_user = user_id

A couple of technical notes to take into consideration:

- All listeners must be explicitly marked via decorator, :meth:`~.cog.Cog.listener`.
- The name of the cog is automatically derived from the class name but can be overridden. See :ref:`vk_api_cogs_meta_options`.
- All commands must now take a ``self`` parameter to allow usage of instance attributes that can be used to maintain state.

Cog Registration
-------------------

Once you have defined your cogs, you need to tell the bot to register the cogs to be used. We do this via the :meth:`~.bot.Bot.add_cog` method.

.. code-block:: python3

    bot.add_cog(Greetings(bot))

This binds the cog to the bot, adding all commands and listeners to the bot automatically.

Note that we reference the cog by name, which we can override through :ref:`vk_api_cogs_meta_options`. So if we ever want to remove the cog eventually, we would have to do the following.

.. code-block:: python3

    bot.remove_cog('Greetings')

Using Cogs
-------------

Just as we remove a cog by its name, we can also retrieve it by its name as well. This allows us to use a cog as an inter-command communication protocol to share data. For example:

.. code-block:: python3
    :emphasize-lines: 22,24

    class Economy(cog.Cog):
        ...

        async def withdraw_money(self, member, money):
            # implementation here
            ...

        async def deposit_money(self, member, money):
            # implementation here
            ...

    class Gambling(cog.Cog):
        def __init__(self, bot):
            self.bot = bot

        def coinflip(self):
            return random.randint(0, 1)

        @commands.command()
        async def gamble(self, ctx, money: int):
            """Gambles some money."""
            economy = self.bot.get_cog('Economy')
            if economy is not None:
                await economy.withdraw_money(ctx.author, money)
                if self.coinflip() == 1:
                    await economy.deposit_money(ctx.author, money * 1.5)

.. _vk_api_cogs_special_methods:

Special Methods
-----------------

As cogs get more complicated and have more commands, there comes a point where we want to customise the behaviour of the entire cog or bot.

They are as follows:

- :meth:`.Cog.cog_unload`
- :meth:`.Cog.cog_check`
- :meth:`.Cog.cog_command_error`
- :meth:`.Cog.cog_before_invoke`
- :meth:`.Cog.cog_after_invoke`
- :meth:`.Cog.bot_check`
- :meth:`.Cog.bot_check_once`

You can visit the reference to get more detail.

.. _vk_api_cogs_meta_options:

Meta Options
--------------

At the heart of a cog resides a metaclass, :class:`.cog.CogMeta`, which can take various options to customise some of the behaviour. To do this, we pass keyword arguments to the class definition line. For example, to change the cog name we can pass the ``name`` keyword argument as follows:

.. code-block:: python3

    class MyCog(cog.Cog, name='My Cog'):
        pass

To see more options that you can set, see the documentation of :class:`.cog.CogMeta`.

Inspection
------------

Since cogs ultimately are classes, we have some tools to help us inspect certain properties of the cog.


To get a :class:`list` of commands, we can use :meth:`.Cog.get_commands`. ::

    >>> cog = bot.get_cog('Greetings')
    >>> commands = cog.get_commands()
    >>> print([c.name for c in commands])

To do the same with listeners, we can query them with :meth:`.Cog.get_listeners`. This returns a list of tuples -- the first element being the listener name and the second one being the actual function itself. ::

    >>> for name, func in cog.get_listeners():
    ...     print(name, '->', func)
