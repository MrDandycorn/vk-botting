"""
The MIT License (MIT)

Copyright (c) 2019-2020 MrDandycorn

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import inspect
import sys
import traceback
import asyncio
import importlib
import types
import collections
import re

from vk_botting.commands import GroupMixin
from vk_botting.utils import async_all, maybe_coroutine, find
from vk_botting.exceptions import NoEntryPointError, ExtensionFailed, ExtensionAlreadyLoaded, ExtensionNotFound, ExtensionNotLoaded, CommandError, CommandNotFound
from vk_botting.context import Context
from vk_botting.view import StringView
from vk_botting.client import Client, UserClient
from vk_botting.cog import Cog


def when_mentioned(bot, msg):
    r"""A callable that implements a command prefix equivalent to being mentioned.
    These are meant to be passed into the :attr:`.Bot.command_prefix` attribute.
    """
    match = re.match(r'\[club{}\|[^\]]+\],? '.format(bot.group.id), msg.text)
    if match and msg.text.startswith(match.group()):
        return [match.group()]
    return ['[club{0.group.id}|@{0.group.screen_name}] '.format(bot), '[club{0.group.id}|{0.group.name}] '.format(bot)]


def when_mentioned_or(*prefixes):
    """A callable that implements when mentioned or other prefixes provided.
    These are meant to be passed into the :attr:`.Bot.command_prefix` attribute.

    Example
    --------

    .. code-block:: python3

        bot = Bot(command_prefix=commands.when_mentioned_or('!'))


    .. note::
        This callable returns another callable, so if this is done inside a custom
        callable, you must call the returned callable, for example:

        .. code-block:: python3

            async def get_prefix(bot, message):
                extras = await prefixes_for(message.peer_id) # returns a list
                return commands.when_mentioned_or(*extras)(bot, message)


    See Also
    ----------
    :func:`.when_mentioned`
    :func:`.when_mentioned_or_pm`
    :func:`.when_mentioned_or_pm_or`
    """
    def inner(bot, msg):
        r = list(prefixes)
        r = when_mentioned(bot, msg) + r
        return r

    return inner


def when_mentioned_or_pm():
    """A callable that implements when mentioned or bot gets pm.
    These are meant to be passed into the :attr:`.Bot.command_prefix` attribute.

    Example
    --------
    
    .. code-block:: python3
    
        bot = commands.Bot(command_prefix=commands.when_mentioned_or_pm())
        
        
    See Also
    ----------
    :func:`.when_mentioned`
    :func:`.when_mentioned_or`
    :func:`.when_mentioned_or_pm_or`
    """
    def inner(bot, msg):
        r = when_mentioned(bot, msg) + [''] if msg.peer_id == msg.from_id else when_mentioned(bot, msg)
        return r

    return inner


def when_mentioned_or_pm_or(*prefixes):
    """A callable that implements when mentioned, pm or other prefixes provided.
    These are meant to be passed into the :attr:`.Bot.command_prefix` attribute.

    Example
    --------
    
    .. code-block:: python3
    
        bot = commands.Bot(command_prefix=commands.when_mentioned_or_pm_or('!'))
        
    .. note::
    
        This callable returns another callable, so if this is done inside a custom
        callable, you must call the returned callable, for example:
        
        .. code-block:: python3

            async def get_prefix(bot, message):
                extras = await prefixes_for(message.peer_id) # returns a list
                return commands.when_mentioned_or(*extras)(bot, message)
                
                
    See Also
    ----------
    :func:`.when_mentioned`
    :func:`.when_mentioned_or`
    :func:`.when_mentioned_or_pm`
    """
    def inner(bot, msg):
        r = list(prefixes)
        r = when_mentioned(bot, msg) + r + [''] if msg.peer_id == msg.from_id else when_mentioned(bot, msg) + r
        return r

    return inner


def _is_submodule(parent, child):
    return parent == child or child.startswith(parent + ".")


class BotBase(GroupMixin):
    def __init__(self, command_prefix, description=None, **options):
        super().__init__(**options)
        self.command_prefix = command_prefix
        self.extra_events = {}
        self.__cogs = {}
        self.__extensions = {}
        self._checks = []
        self._check_once = []
        self._before_invoke = None
        self._after_invoke = None
        self.description = inspect.cleandoc(description) if description else ''
        self.owner_id = options.get('owner_id')

        if options.pop('self_bot', False):
            self._skip_check = lambda x, y: x != y
        else:
            self._skip_check = lambda x, y: x == y

    def dispatch(self, event_name, *args, **kwargs):
        super().dispatch(event_name, *args, **kwargs)
        ev = 'on_' + event_name
        for event in self.extra_events.get(ev, []):
            self._schedule_event(event, ev, *args, **kwargs)

    async def close(self):
        for extension in tuple(self.__extensions):
            try:
                self.unload_extension(extension)
            except Exception:
                pass

        for cog in tuple(self.__cogs):
            try:
                self.remove_cog(cog)
            except Exception:
                pass

        await super().close()

    async def on_command_error(self, context, exception):
        """|coro|
        The default command error handler provided by the bot.
        By default this prints to :data:`sys.stderr` however it could be
        overridden to have a different implementation.
        This only fires if you do not specify any listeners for command error.
        """
        if self.extra_events.get('on_command_error', None):
            return

        if hasattr(context.command, 'on_error'):
            return

        cog = context.cog
        if cog:
            if Cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        print('Ignoring exception in command {}:'.format(context.command), file=sys.stderr)
        traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

    def check(self, func):
        r"""A decorator that adds a global check to the bot.
        A global check is similar to a :func:`.check` that is applied
        on a per command basis except it is run before any command checks
        have been verified and applies to every command the bot has.
        
        .. note::
        
            This function can either be a regular function or a coroutine.
            
        Similar to a command :func:`.check`\, this takes a single parameter
        of type :class:`.Context` and can only raise exceptions inherited from
        :exc:`.CommandError`.
        Example
        ---------
        
        .. code-block:: python3
        
            @bot.check
            def check_commands(ctx):
                return ctx.command.qualified_name in allowed_commands
                
        """
        self.add_check(func)
        return func

    def add_check(self, func, *, call_once=False):
        """Adds a global check to the bot.
        This is the non-decorator interface to :meth:`.check`
        and :meth:`.check_once`.
        
        Parameters
        -----------
        func
            The function that was used as a global check.
        call_once: :class:`bool`
            If the function should only be called once per
            :meth:`Command.invoke` call.
        """
        if call_once:
            self._check_once.append(func)
        else:
            self._checks.append(func)

    def remove_check(self, func, *, call_once=False):
        """Removes a global check from the bot.
        This function is idempotent and will not raise an exception
        if the function is not in the global checks.
        
        Parameters
        -----------
        func
            The function to remove from the global checks.
        call_once: :class:`bool`
            If the function was added with ``call_once=True`` in
            the :meth:`.Bot.add_check` call or using :meth:`.check_once`.
        """
        l = self._check_once if call_once else self._checks

        try:
            l.remove(func)
        except ValueError:
            pass

    def check_once(self, func):
        r"""A decorator that adds a "call once" global check to the bot.
        Unlike regular global checks, this one is called only once
        per :meth:`Command.invoke` call.
        Regular global checks are called whenever a command is called
        or :meth:`.Command.can_run` is called. This type of check
        bypasses that and ensures that it's called only once, even inside
        the default help command.
        
        .. note::
        
            This function can either be a regular function or a coroutine.
            
        Similar to a command :func:`.check`\, this takes a single parameter
        of type :class:`.Context` and can only raise exceptions inherited from
        :exc:`.CommandError`.
        
        Example
        ---------
        
        .. code-block:: python3
        
            @bot.check_once
            def whitelist(ctx):
                return ctx.message.author.id in my_whitelist
                
        """
        self.add_check(func, call_once=True)
        return func

    async def can_run(self, ctx, *, call_once=False):
        data = self._check_once if call_once else self._checks

        if len(data) == 0:
            return True

        return await async_all(f(ctx) for f in data)

    def before_invoke(self, coro):
        """A decorator that registers a coroutine as a pre-invoke hook.
        A pre-invoke hook is called directly before the command is
        called. This makes it a useful function to set up database
        connections or any type of set up required.
        This pre-invoke hook takes a sole parameter, a :class:`.Context`.
        
        .. note::
        
            The :meth:`~.Bot.before_invoke` and :meth:`~.Bot.after_invoke` hooks are
            only called if all checks and argument parsing procedures pass
            without error. If any check or argument parsing procedures fail
            then the hooks are not called.
            
        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the pre-invoke hook.
            
        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The pre-invoke hook must be a coroutine.')

        self._before_invoke = coro
        return coro

    def after_invoke(self, coro):
        r"""A decorator that registers a coroutine as a post-invoke hook.
        A post-invoke hook is called directly after the command is
        called. This makes it a useful function to clean-up database
        connections or any type of clean up required.
        This post-invoke hook takes a sole parameter, a :class:`.Context`.
        
        .. note::
            Similar to :meth:`~.Bot.before_invoke`\, this is not called unless
            checks and argument parsing procedures succeed. This hook is,
            however, **always** called regardless of the internal command
            callback raising an error (i.e. :exc:`.CommandInvokeError`\).
            This makes it ideal for clean-up scenarios.
            
        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the post-invoke hook.
            
        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The post-invoke hook must be a coroutine.')

        self._after_invoke = coro
        return coro

    def add_listener(self, func, name=None):
        """The non decorator alternative to :meth:`.listen`.
        
        Parameters
        -----------
        func: :ref:`coroutine <coroutine>`
            The function to call.
        name: Optional[:class:`str`]
            The name of the event to listen for. Defaults to ``func.__name__``.
            
        Example
        --------
        
        .. code-block:: python3
        
            async def on_ready(): pass
            async def my_message(message): pass
            bot.add_listener(on_ready)
            bot.add_listener(my_message, 'on_message_new')
            
        """
        name = func.__name__ if name is None else name

        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Listeners must be coroutines')

        if name in self.extra_events:
            self.extra_events[name].append(func)
        else:
            self.extra_events[name] = [func]

    def remove_listener(self, func, name=None):
        """Removes a listener from the pool of listeners.
        
        Parameters
        -----------
        func
            The function that was used as a listener to remove.
        name: :class:`str`
            The name of the event we want to remove. Defaults to
            ``func.__name__``.
        """
        name = func.__name__ if name is None else name

        if name in self.extra_events:
            try:
                self.extra_events[name].remove(func)
            except ValueError:
                pass

    def listen(self, name=None):
        """A decorator that registers another function as an external
        event listener. Basically this allows you to listen to multiple
        events from different places e.g. such as :func:`.on_ready`
        The functions being listened to must be a :ref:`coroutine <coroutine>`.
        
        Example
        --------
        
        .. code-block:: python3
        
            @bot.listen()
            async def on_message_new(message):
                print('one')
            # in some other file...
            @bot.listen('on_message_new')
            async def my_message(message):
                print('two')

        Would print one and two in an unspecified order.
        Raises
        -------
        TypeError
            The function being listened to is not a coroutine.
        """
        def decorator(func):
            self.add_listener(func, name)
            return func

        return decorator

    def add_cog(self, cog):
        """Adds a "cog" to the bot.
        A cog is a class that has its own event listeners and commands.
        
        Parameters
        -----------
        cog: :class:`.Cog`
            The cog to register to the bot.
            
        Raises
        -------
        TypeError
            The cog does not inherit from :class:`.Cog`.
        CommandError
            An error happened during loading.
        """
        if not isinstance(cog, Cog):
            raise TypeError('cogs must derive from Cog')

        cog = cog._inject(self)
        self.__cogs[cog.__cog_name__] = cog

    def get_cog(self, name):
        """Gets the cog instance requested.
        If the cog is not found, ``None`` is returned instead.
        
        Parameters
        -----------
        name: :class:`str`
            The name of the cog you are requesting.
            This is equivalent to the name passed via keyword
            argument in class creation or the class name if unspecified.
        """
        return self.__cogs.get(name)

    def remove_cog(self, name):
        """Removes a cog from the bot.
        All registered commands and event listeners that the
        cog has registered will be removed as well.
        If no cog is found then this method has no effect.
        
        Parameters
        -----------
        name: :class:`str`
            The name of the cog to remove.
        """
        cog = self.__cogs.pop(name, None)
        if cog is None:
            return
        cog._eject(self)

    @property
    def cogs(self):
        """Mapping[:class:`str`, :class:`Cog`]: A read-only mapping of cog name to cog."""
        return types.MappingProxyType(self.__cogs)

    def _remove_module_references(self, name):
        for cogname, cog in self.__cogs.copy().items():
            if _is_submodule(name, cog.__module__):
                self.remove_cog(cogname)

        for cmd in self.all_commands.copy().values():
            if cmd.module is not None and _is_submodule(name, cmd.module):
                if isinstance(cmd, GroupMixin):
                    cmd.recursively_remove_all_commands()
                self.remove_command(cmd.name)

        for event_list in self.extra_events.copy().values():
            remove = []
            for index, event in enumerate(event_list):
                if event.__module__ is not None and _is_submodule(name, event.__module__):
                    remove.append(index)

            for index in reversed(remove):
                del event_list[index]

    def _call_module_finalizers(self, lib, key):
        try:
            func = getattr(lib, 'teardown')
        except AttributeError:
            pass
        else:
            try:
                func(self)
            except Exception:
                pass
        finally:
            self.__extensions.pop(key, None)
            sys.modules.pop(key, None)
            name = lib.__name__
            for module in list(sys.modules.keys()):
                if _is_submodule(name, module):
                    del sys.modules[module]

    def _load_from_module_spec(self, lib, key):
        try:
            setup = getattr(lib, 'setup')
        except AttributeError:
            del sys.modules[key]
            raise NoEntryPointError(key)

        try:
            setup(self)
        except Exception as e:
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, key)
            raise ExtensionFailed(key, e) from e
        else:
            self.__extensions[key] = lib

    def load_extension(self, name):
        """Loads an extension.
        An extension is a python module that contains commands, cogs, or
        listeners.
        An extension must have a global function, ``setup`` defined as
        the entry point on what to do when the extension is loaded. This entry
        point must have a single argument, the ``bot``.
        
        Parameters
        ------------
        name: :class:`str`
            The extension name to load. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
            
        Raises
        --------
        ExtensionNotFound
            The extension could not be imported.
        ExtensionAlreadyLoaded
            The extension is already loaded.
        NoEntryPointError
            The extension does not have a setup function.
        ExtensionFailed
            The extension or its setup function had an execution error.
        """
        if name in self.__extensions:
            raise ExtensionAlreadyLoaded(name)

        try:
            lib = importlib.import_module(name)
        except ImportError as e:
            raise ExtensionNotFound(name, e) from e
        else:
            self._load_from_module_spec(lib, name)

    def unload_extension(self, name):
        """Unloads an extension.
        When the extension is unloaded, all commands, listeners, and cogs are
        removed from the bot and the module is un-imported.
        The extension can provide an optional global function, ``teardown``,
        to do miscellaneous clean-up if necessary. This function takes a single
        parameter, the ``bot``, similar to ``setup`` from
        :meth:`~.Bot.load_extension`.
        
        Parameters
        ------------
        name: :class:`str`
            The extension name to unload. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
            
        Raises
        -------
        ExtensionNotLoaded
            The extension was not loaded.
        """
        lib = self.__extensions.get(name)
        if lib is None:
            raise ExtensionNotLoaded(name)

        self._remove_module_references(lib.__name__)
        self._call_module_finalizers(lib, name)

    def reload_extension(self, name):
        """Atomically reloads an extension.
        This replaces the extension with the same extension, only refreshed. This is
        equivalent to a :meth:`unload_extension` followed by a :meth:`load_extension`
        except done in an atomic way. That is, if an operation fails mid-reload then
        the bot will roll-back to the prior working state.
        
        Parameters
        ------------
        name: :class:`str`
            The extension name to reload. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
            
        Raises
        -------
        ExtensionNotLoaded
            The extension was not loaded.
        ExtensionNotFound
            The extension could not be imported.
        NoEntryPointError
            The extension does not have a setup function.
        ExtensionFailed
            The extension setup function had an execution error.
        """
        lib = self.__extensions.get(name)
        if lib is None:
            raise ExtensionNotLoaded(name)

        modules = {
            name: module
            for name, module in sys.modules.items()
            if _is_submodule(lib.__name__, name)
        }

        try:
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, name)
            self.load_extension(name)
        except Exception as e:
            self._load_from_module_spec(lib, name)
            sys.modules.update(modules)
            raise

    @property
    def extensions(self):
        """Mapping[:class:`str`, :class:`py:types.ModuleType`]: A read-only mapping of extension name to extension."""
        return types.MappingProxyType(self.__extensions)

    async def get_prefix(self, message):
        """|coro|
        
        Retrieves the prefix the bot is listening to
        with the message as a context.
        
        Parameters
        -----------
        message: :class:`.Message`
            The message context to get the prefix of.
            
        Returns
        --------
        Union[List[:class:`str`], :class:`str`]
            A list of prefixes or a single prefix that the bot is
            listening for.
        """
        prefix = ret = self.command_prefix
        if callable(prefix):
            ret = await maybe_coroutine(prefix, self, message)

        if not isinstance(ret, str):
            try:
                ret = list(ret)
            except TypeError:
                if isinstance(ret, collections.Iterable):
                    raise

                raise TypeError("command_prefix must be plain string, iterable of strings, or callable "
                                "returning either of these, not {}".format(ret.__class__.__name__))

            if not ret:
                raise ValueError("Iterable command_prefix must contain at least one prefix")

        return ret

    async def get_context(self, message, *, cls=Context):
        r"""|coro|
        
        Returns the invocation context from the message.
        This is a more low-level counter-part for :meth:`.process_commands`
        to allow users more fine grained control over the processing.
        The returned context is not guaranteed to be a valid invocation
        context, :attr:`.Context.valid` must be checked to make sure it is.
        If the context is not valid then it is not a valid candidate to be
        invoked under :meth:`~.Bot.invoke`.
        
        Parameters
        -----------
        message: :class:`.Message`
            The message to get the invocation context from.
        cls
            The factory class that will be used to create the context.
            By default, this is :class:`.Context`. Should a custom
            class be provided, it must be similar enough to :class:`.Context`\'s
            interface.
        Returns
        --------
        :class:`.Context`
            The invocation context. The type of this can change via the
            ``cls`` parameter.
        """
        view = StringView(message.text)
        ctx = cls(prefix=None, view=view, bot=self, message=message)

        if self._skip_check(message.peer_id, self.group.id):
            return ctx

        prefix = await self.get_prefix(message)
        invoked_prefix = prefix

        if isinstance(prefix, str):
            if not view.skip_string(prefix):
                return ctx
        else:
            try:
                if message.text.startswith(tuple(prefix)):
                    invoked_prefix = find(view.skip_string, prefix)
                else:
                    return ctx

            except TypeError:
                if not isinstance(prefix, list):
                    raise TypeError("get_prefix must return either a string or a list of string, "
                                    "not {}".format(prefix.__class__.__name__))

                for value in prefix:
                    if not isinstance(value, str):
                        raise TypeError("Iterable command_prefix or list returned from get_prefix must "
                                        "contain only strings, not {}".format(value.__class__.__name__))

                raise

        msg = view.read_rest()
        view.undo()
        # This is by far the fastest method there is as far as my knowledge extends
        # Considering VK message length limit is 4096 it is at most 2048 iterations which is at most about 50 ms
        # If not exaggerating the length of user messages this is the most optimal way imo
        # It also works well with several commands having the same beginning as it will always choose the longest one
        commands = set(self.all_commands) if not self.case_insensitive else self.all_commands
        words = msg.split(' ')
        for wordamt in range(len(words), 1, -1):
            potcomm = ' '.join(words[:wordamt])
            if potcomm in commands:
                invoker = potcomm
                view.read(len(invoker))
                break
        else:
            invoker = view.get_word()
        ctx.invoked_with = invoker
        ctx.prefix = invoked_prefix
        ctx.command = self.all_commands.get(invoker)
        return ctx

    async def invoke(self, ctx):
        """|coro|
        
        Invokes the command given under the invocation context and
        handles all the internal event dispatch mechanisms.
        
        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context to invoke.
        """
        if ctx.command is not None:
            self.dispatch('command', ctx)
            try:
                if await self.can_run(ctx, call_once=True):
                    await ctx.command.invoke(ctx)
            except CommandError as exc:
                await ctx.command.dispatch_error(ctx, exc)
            else:
                self.dispatch('command_completion', ctx)
        elif ctx.invoked_with:
            exc = CommandNotFound('Command "{}" is not found'.format(ctx.invoked_with))
            self.dispatch('command_error', ctx, exc)

    async def process_commands(self, message):
        """|coro|
        
        This function processes the commands that have been registered
        to the bot and other groups. Without this coroutine, none of the
        commands will be triggered.
        
        By default, this coroutine is called inside the :func:`.on_message_new`
        event. If you choose to override the :func:`.on_message_new` event, then
        you should invoke this coroutine as well.
        
        This is built using other low level tools, and is equivalent to a
        call to :meth:`~.Bot.get_context` followed by a call to :meth:`~.Bot.invoke`.
        
        This also checks if the message's author is a bot and doesn't
        call :meth:`~.Bot.get_context` or :meth:`~.Bot.invoke` if so.
        
        Parameters
        -----------
        message: :class:`.Message`
            The message to process commands for.
        """
        if message.peer_id == self.group.id:
            return

        ctx = await self.get_context(message)
        await self.invoke(ctx)

    async def on_message_new(self, message):
        await self.process_commands(message)


class Bot(BotBase, Client):
    """Represents a VK bot.
    This class is a subclass of :class:`vk_botting.client.Client` and as a result
    anything that you can do with a :class:`vk_botting.client.Client` you can do with
    this bot.
    
    This class also subclasses :class:`.GroupMixin` to provide the functionality
    to manage commands.
    
    Attributes
    -----------
    command_prefix
        The command prefix is what the message content must contain initially
        to have a command invoked. This prefix could either be a string to
        indicate what the prefix should be, or a callable that takes in the bot
        as its first parameter and :class:`.Message` as its second
        parameter and returns the prefix. This is to facilitate "dynamic"
        command prefixes. This callable can be either a regular function or
        a coroutine.
        
        The command prefix could also be an iterable of strings indicating that
        multiple checks for the prefix should be used and the first one to
        match will be the invocation prefix. You can get this prefix via
        :attr:`.Context.prefix`. To avoid confusion empty iterables are not
        allowed.
        
        .. note::
        
            When passing multiple prefixes be careful to not pass a prefix
            that matches a longer prefix occurring later in the sequence.  For
            example, if the command prefix is ``('!', '!?')``  the ``'!?'``
            prefix will never be matched to any message as the previous one
            matches messages starting with ``!?``. This is especially important
            when passing an empty string, it should always be last as no prefix
            after it will be matched.
            
    case_insensitive: :class:`bool`
        Whether the commands should be case insensitive. Defaults to ``False``. This
        attribute does not carry over to groups. You must set it to every group if
        you require group commands to be case insensitive as well.
    self_bot: :class:`bool`
        If ``True``, the bot will only listen to commands invoked by itself rather
        than ignoring itself. If ``False`` (the default) then the bot will ignore
        itself. This cannot be changed once initialised.
    v: :class:`str`
        VK API version. Defaults to '5.999' (current latest)

        .. warning::

            Library is not intended to use with API Version lower than '5.103'

    force: :class:`bool`
        If bot should force optimal longpoll settings automatically
    lang: :class:`str`
        Lang parameter for API requests
    """
    pass


class UserBot(BotBase, UserClient):    
    """Represents a VK user-bot.
    This class is a subclass of :class:`vk_botting.client.UserClient` and as a result
    anything that you can do with a :class:`vk_botting.client.UserClient` you can do with
    this bot.
    
    This class also subclasses :class:`.GroupMixin` to provide the functionality
    to manage commands.
    
    Attributes
    -----------
    command_prefix
        The command prefix is what the message content must contain initially
        to have a command invoked. This prefix could either be a string to
        indicate what the prefix should be, or a callable that takes in the bot
        as its first parameter and :class:`.Message` as its second
        parameter and returns the prefix. This is to facilitate "dynamic"
        command prefixes. This callable can be either a regular function or
        a coroutine.
        
        The command prefix could also be an iterable of strings indicating that
        multiple checks for the prefix should be used and the first one to
        match will be the invocation prefix. You can get this prefix via
        :attr:`.Context.prefix`. To avoid confusion empty iterables are not
        allowed.
        
        .. note::
        
            When passing multiple prefixes be careful to not pass a prefix
            that matches a longer prefix occurring later in the sequence.  For
            example, if the command prefix is ``('!', '!?')``  the ``'!?'``
            prefix will never be matched to any message as the previous one
            matches messages starting with ``!?``. This is especially important
            when passing an empty string, it should always be last as no prefix
            after it will be matched.
            
    case_insensitive: :class:`bool`
        Whether the commands should be case insensitive. Defaults to ``False``. This
        attribute does not carry over to group commands. You must set it to every group command if
        you require group commands to be case insensitive as well.
    self_bot: :class:`bool`
        If ``True``, the bot will only listen to commands invoked by itself rather
        than ignoring itself. If ``False`` (the default) then the bot will ignore
        itself. This cannot be changed once initialised.
    v: :class:`str`
        VK API version. Defaults to '5.999' (current latest)

        .. warning::

            Library is not intended to use with API Version lower than '5.103'

    force: :class:`bool`
        If bot should force optimal longpoll settings automatically
    lang: :class:`str`
        Lang parameter for API requests
    """
    pass
