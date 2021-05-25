"""
The MIT License (MIT)

Original work Copyright (c) 2015-present Rapptz
Modified work Copyright (c) 2019-present MrDandycorn

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

from vk_botting._types import _BaseCommand

__all__ = (
    'CogMeta',
    'Cog',
)


class CogMeta(type):
    """A metaclass for defining a cog.
    
    Note that you should probably not use this directly. It is exposed
    purely for documentation purposes along with making custom metaclasses to intermix
    with other metaclasses such as the :class:`abc.ABCMeta` metaclass.
    
    For example, to create an abstract cog mixin class, the following would be done.
    
    .. code-block:: python3
    
        import abc
        class CogABCMeta(CogMeta, abc.ABCMeta):
            pass
        class SomeMixin(metaclass=abc.ABCMeta):
            pass
        class SomeCogMixin(SomeMixin, Cog, metaclass=CogABCMeta):
            pass
            
    .. note::
    
        When passing an attribute of a metaclass that is documented below, note
        that you must pass it as a keyword-only argument to the class creation
        like the following example:
        
        .. code-block:: python3
        
            class MyCog(Cog, name='My Cog'):
                pass
                
    Attributes
    -----------
    name: :class:`str`
        The cog name. By default, it is the name of the class with no modification.
    command_attrs: :class:`dict`
        A list of attributes to apply to every command inside this cog. The dictionary
        is passed into the :class:`Command` (or its subclass) options at ``__init__``.
        If you specify attributes inside the command attribute in the class, it will
        override the one specified inside this attribute. For example:
        
        .. code-block:: python3
        
            class MyCog(Cog, command_attrs=dict(hidden=True)):
                @command()
                async def foo(self, ctx):
                    pass # hidden -> True
                    
                @command(hidden=False)
                async def bar(self, ctx):
                    pass # hidden -> False
                    
    """
    def __new__(mcs, *args, **kwargs):
        name, bases, attrs = args
        attrs['__cog_name__'] = kwargs.pop('name', name)
        attrs['__cog_settings__'] = command_attrs = kwargs.pop('command_attrs', {})

        commands = {}
        listeners = {}
        no_bot_cog = 'Commands or listeners must not start with cog_ or bot_ (in method {0.__name__}.{1})'

        new_cls = super().__new__(mcs, name, bases, attrs, **kwargs)
        for base in reversed(new_cls.__mro__):
            for elem, value in base.__dict__.items():
                if elem in commands:
                    del commands[elem]
                if elem in listeners:
                    del listeners[elem]

                is_static_method = isinstance(value, staticmethod)
                if is_static_method:
                    value = value.__func__
                if isinstance(value, _BaseCommand):
                    if is_static_method:
                        raise TypeError('Command in method {0}.{1!r} must not be staticmethod.'.format(base, elem))
                    if elem.startswith(('cog_', 'bot_')):
                        raise TypeError(no_bot_cog.format(base, elem))
                    commands[elem] = value
                elif inspect.iscoroutinefunction(value):
                    try:
                        is_listener = getattr(value, '__cog_listener__')
                    except AttributeError:
                        continue
                    else:
                        if elem.startswith(('cog_', 'bot_')):
                            raise TypeError(no_bot_cog.format(base, elem))
                        listeners[elem] = value

        new_cls.__cog_commands__ = list(commands.values())  # this will be copied in Cog.__new__

        listeners_as_list = []
        for listener in listeners.values():
            for listener_name in listener.__cog_listener_names__:
                listeners_as_list.append((listener_name, listener.__name__))

        new_cls.__cog_listeners__ = listeners_as_list
        return new_cls

    def __init__(cls, *args, **kwargs):
        super().__init__(*args)

    @classmethod
    def qualified_name(mcs):
        return mcs.__cog_name__


def _cog_special_method(func):
    func.__cog_special_method__ = None
    return func


class Cog(metaclass=CogMeta):
    """The base class that all cogs must inherit from.
    
    A cog is a collection of commands, listeners, and optional state to
    help group commands together. More information on them can be found on
    the :ref:`vk_api_cogs` page.
    
    When inheriting from this class, the options shown in :class:`CogMeta`
    are equally valid here.
    """
    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        cmd_attrs = cls.__cog_settings__

        self.__cog_commands__ = tuple(c._update_copy(cmd_attrs) for c in cls.__cog_commands__)

        lookup = {
            cmd.qualified_name: cmd
            for cmd in self.__cog_commands__
        }

        for command in self.__cog_commands__:
            setattr(self, command.callback.__name__, command)
            parent = command.parent
            if parent is not None:
                parent = lookup[parent.qualified_name]

                removed = parent.remove_command(command.name)
                parent.add_command(command)

        return self

    def get_commands(self):
        return [c for c in self.__cog_commands__ if c.parent is None]

    @property
    def qualified_name(self):
        """:class:`str`: Returns the cog's specified name, not the class name."""
        return self.__cog_name__

    @property
    def description(self):
        """:class:`str`: Returns the cog's description, typically the cleaned docstring."""
        try:
            return self.__cog_cleaned_doc__
        except AttributeError:
            self.__cog_cleaned_doc__ = cleaned = inspect.getdoc(self)
            return cleaned

    def walk_commands(self):
        """An iterator that recursively walks through this cog's commands and subcommands."""
        from vk_botting.commands import GroupMixin
        for command in self.__cog_commands__:
            if command.parent is None:
                yield command
                if isinstance(command, GroupMixin):
                    yield from command.walk_commands()

    def get_listeners(self):
        """Returns a :class:`list` of (name, function) listener pairs that are defined in this cog."""
        return [(name, getattr(self, method_name)) for name, method_name in self.__cog_listeners__]

    @classmethod
    def _get_overridden_method(cls, method):
        """Return None if the method is not overridden. Otherwise returns the overridden method."""
        return getattr(method.__func__, '__cog_special_method__', method)

    @classmethod
    def listener(cls, name=None):
        """A decorator that marks a function as a listener.
        
        This is the cog equivalent of :meth:`.Bot.listen`.
        
        Parameters
        ------------
        name: :class:`str`
            The name of the event being listened to. If not provided, it
            defaults to the function's name.
            
        Raises
        --------
        TypeError
            The function is not a coroutine function or a string was not passed as
            the name.
        """
        if name is not None and not isinstance(name, str):
            raise TypeError('Cog.listener expected str but received {0.__class__.__name__!r} instead.'.format(name))

        def decorator(func):
            actual = func
            if isinstance(actual, staticmethod):
                actual = actual.__func__
            if not inspect.iscoroutinefunction(actual):
                raise TypeError('Listener function must be a coroutine function.')
            actual.__cog_listener__ = True
            to_assign = name or actual.__name__
            try:
                actual.__cog_listener_names__.append(to_assign)
            except AttributeError:
                actual.__cog_listener_names__ = [to_assign]
            return func

        return decorator

    @_cog_special_method
    def cog_unload(self):
        """A special method that is called when the cog gets removed.
        
        This function **cannot** be a coroutine. It must be a regular
        function.
        
        Subclasses must replace this if they want special unloading behaviour.
        """
        pass

    @_cog_special_method
    def bot_check_once(self, ctx):
        """A special method that registers as a :meth:`.Bot.check_once`
        check.
        
        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_cog_special_method
    def bot_check(self, ctx):
        """A special method that registers as a :meth:`.Bot.check_once`
        check.
        
        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_cog_special_method
    def cog_check(self, ctx):
        """A special method that registers as a :func:`commands.check`
        for every command and subcommand in this cog.
        
        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_cog_special_method
    def cog_command_error(self, ctx, error):
        """A special method that is called whenever an error
        is dispatched inside this cog.
        
        This is similar to :func:`.on_command_error` except only applying
        to the commands inside this cog.
        
        This function **can** be a coroutine.
        
        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context where the error happened.
        error: :class:`CommandError`
            The error that happened.
        """
        pass

    @_cog_special_method
    async def cog_before_invoke(self, ctx):
        """A special method that acts as a cog local pre-invoke hook.
        This is similar to :meth:`.Command.before_invoke`.
        
        This **must** be a coroutine.
        
        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context.
        """
        pass

    @_cog_special_method
    async def cog_after_invoke(self, ctx):
        """A special method that acts as a cog local post-invoke hook.
        This is similar to :meth:`.Command.after_invoke`.
        
        This **must** be a coroutine.
        
        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context.
        """
        pass

    def _inject(self, bot):
        cls = self.__class__

        for index, command in enumerate(self.__cog_commands__):
            command.cog = self
            if command.parent is None:
                try:
                    bot.add_command(command)
                except Exception as e:
                    for to_undo in self.__cog_commands__[:index]:
                        bot.remove_command(to_undo)
                    raise e

        if cls.bot_check is not Cog.bot_check:
            bot.add_check(self.bot_check)

        if cls.bot_check_once is not Cog.bot_check_once:
            bot.add_check(self.bot_check_once, call_once=True)

        for name, method_name in self.__cog_listeners__:
            bot.add_listener(getattr(self, method_name), name)

        return self

    def _eject(self, bot):
        cls = self.__class__

        try:
            for command in self.__cog_commands__:
                if command.parent is None:
                    bot.remove_command(command.name)

            for _, method_name in self.__cog_listeners__:
                bot.remove_listener(getattr(self, method_name))

            if cls.bot_check is not Cog.bot_check:
                bot.remove_check(self.bot_check)

            if cls.bot_check_once is not Cog.bot_check_once:
                bot.remove_check(self.bot_check_once, call_once=True)
        finally:
            self.cog_unload()
