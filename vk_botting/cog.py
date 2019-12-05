import inspect
from _types import _BaseCommand

__all__ = (
    'CogMeta',
    'Cog',
)


class CogMeta(type):
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
        return self.__cog_name__

    @property
    def description(self):
        try:
            return self.__cog_cleaned_doc__
        except AttributeError:
            self.__cog_cleaned_doc__ = cleaned = inspect.getdoc(self)
            return cleaned

    def walk_commands(self):
        from .commands import GroupMixin
        for command in self.__cog_commands__:
            if command.parent is None:
                yield command
                if isinstance(command, GroupMixin):
                    yield from command.walk_commands()

    def get_listeners(self):
        return [(name, getattr(self, method_name)) for name, method_name in self.__cog_listeners__]

    @classmethod
    def _get_overridden_method(cls, method):
        return getattr(method.__func__, '__cog_special_method__', method)

    @classmethod
    def listener(cls, name=None):
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
        pass

    @_cog_special_method
    def bot_check_once(self, ctx):
        return True

    @_cog_special_method
    def bot_check(self, ctx):
        return True

    @_cog_special_method
    def cog_check(self, ctx):
        return True

    @_cog_special_method
    def cog_command_error(self, ctx, error):
        pass

    @_cog_special_method
    async def cog_before_invoke(self, ctx):
        pass

    @_cog_special_method
    async def cog_after_invoke(self, ctx):
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
