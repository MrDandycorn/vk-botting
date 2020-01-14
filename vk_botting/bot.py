"""
The MIT License (MIT)

Copyright (c) 2019 MrDandycorn

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
    match = re.match(rf'\[club{bot.group.id}\|[^\]]+\] ', msg.text)
    if match and msg.text.startswith(match.group()):
        return [match.group()]
    return [f'[club{bot.group.id}|@{bot.group.screen_name}] ', f'[club{bot.group.id}|{bot.group.name}] ']


def when_mentioned_or(*prefixes):
    def inner(bot, msg):
        r = list(prefixes)
        r = when_mentioned(bot, msg) + r
        return r

    return inner


def when_mentioned_or_pm():
    def inner(bot, msg):
        r = when_mentioned(bot, msg) + [''] if msg.peer_id == msg.from_id else when_mentioned(bot, msg)
        return r

    return inner


def when_mentioned_or_pm_or(*prefixes):
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
        self.add_check(func)
        return func

    def add_check(self, func, *, call_once=False):
        if call_once:
            self._check_once.append(func)
        else:
            self._checks.append(func)

    def remove_check(self, func, *, call_once=False):
        l = self._check_once if call_once else self._checks

        try:
            l.remove(func)
        except ValueError:
            pass

    def check_once(self, func):
        self.add_check(func, call_once=True)
        return func

    async def can_run(self, ctx, *, call_once=False):
        data = self._check_once if call_once else self._checks

        if len(data) == 0:
            return True

        return await async_all(f(ctx) for f in data)

    async def is_owner(self, user):
        if self.owner_id is None:
            app = await self.application_info()
            self.owner_id = owner_id = app.owner.id
            return user.id == owner_id
        return user.id == self.owner_id

    def before_invoke(self, coro):
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The pre-invoke hook must be a coroutine.')

        self._before_invoke = coro
        return coro

    def after_invoke(self, coro):
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The post-invoke hook must be a coroutine.')

        self._after_invoke = coro
        return coro

    def add_listener(self, func, name=None):
        name = func.__name__ if name is None else name

        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Listeners must be coroutines')

        if name in self.extra_events:
            self.extra_events[name].append(func)
        else:
            self.extra_events[name] = [func]

    def remove_listener(self, func, name=None):
        name = func.__name__ if name is None else name

        if name in self.extra_events:
            try:
                self.extra_events[name].remove(func)
            except ValueError:
                pass

    def listen(self, name=None):
        def decorator(func):
            self.add_listener(func, name)
            return func

        return decorator

    def add_cog(self, cog):
        if not isinstance(cog, Cog):
            raise TypeError('cogs must derive from Cog')

        cog = cog._inject(self)
        self.__cogs[cog.__cog_name__] = cog

    def get_cog(self, name):
        return self.__cogs.get(name)

    def remove_cog(self, name):
        cog = self.__cogs.pop(name, None)
        if cog is None:
            return
        cog._eject(self)

    @property
    def cogs(self):
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
        if name in self.__extensions:
            raise ExtensionAlreadyLoaded(name)

        try:
            lib = importlib.import_module(name)
        except ImportError as e:
            raise ExtensionNotFound(name, e) from e
        else:
            self._load_from_module_spec(lib, name)

    def unload_extension(self, name):
        lib = self.__extensions.get(name)
        if lib is None:
            raise ExtensionNotLoaded(name)

        self._remove_module_references(lib.__name__)
        self._call_module_finalizers(lib, name)

    def reload_extension(self, name):
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
        return types.MappingProxyType(self.__extensions)

    async def get_prefix(self, message):
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
        for command in self.all_commands:
            if self.all_commands[command].has_spaces and ((self.case_insensitive and bool(re.match(command, msg, re.I))) or re.match(command, msg)):
                view.read(len(command))
                ctx.invoked_with = command
                ctx.prefix = invoked_prefix
                ctx.command = self.all_commands[command]
                return ctx
        invoker = view.get_word()
        ctx.invoked_with = invoker
        ctx.prefix = invoked_prefix
        ctx.command = self.all_commands.get(invoker)
        return ctx

    async def invoke(self, ctx):
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
        if message.peer_id == self.group.id:
            return

        ctx = await self.get_context(message)
        await self.invoke(ctx)

    async def on_message_new(self, message):
        await self.process_commands(message)


class Bot(BotBase, Client):
    pass


class UserBot(BotBase, UserClient):
    pass
