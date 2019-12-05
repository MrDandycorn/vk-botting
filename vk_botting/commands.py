import asyncio
import functools
import inspect
import typing
import datetime

from vk_botting.exceptions import CommandError, CommandInvokeError, ClientException, ConversionError, BadArgument, BadUnionArgument, MissingRequiredArgument, TooManyArguments, \
    CheckFailure, DisabledCommand, CommandOnCooldown
import vk_botting.conversions as converters
from vk_botting.cooldowns import CooldownMapping
from vk_botting.utils import async_all, maybe_coroutine
from vk_botting._types import _BaseCommand
from vk_botting.cog import Cog


def wrap_callback(coro):
    @functools.wraps(coro)
    async def wrapped(*args, **kwargs):
        try:
            ret = await coro(*args, **kwargs)
        except CommandError:
            raise
        except asyncio.CancelledError:
            return
        except Exception as exc:
            raise CommandInvokeError(exc) from exc
        return ret

    return wrapped


def hooked_wrapped_callback(command, ctx, coro):
    @functools.wraps(coro)
    async def wrapped(*args, **kwargs):
        try:
            ret = await coro(*args, **kwargs)
        except CommandError:
            ctx.command_failed = True
            raise
        except asyncio.CancelledError:
            ctx.command_failed = True
            return
        except Exception as exc:
            ctx.command_failed = True
            raise CommandInvokeError(exc) from exc
        finally:
            await command.call_after_hooks(ctx)
        return ret

    return wrapped


class GroupMixin:

    def __init__(self, *args, **kwargs):
        case_insensitive = kwargs.get('case_insensitive', False)
        self.all_commands = _CaseInsensitiveDict() if case_insensitive else {}
        self.case_insensitive = case_insensitive
        super().__init__(*args, **kwargs)

    @property
    def commands(self):
        """Set[:class:`.Command`]: A unique set of commands without aliases that are registered."""
        return set(self.all_commands.values())

    def recursively_remove_all_commands(self):
        for command in self.all_commands.copy().values():
            if isinstance(command, GroupMixin):
                command.recursively_remove_all_commands()
            self.remove_command(command.name)

    def add_command(self, command):

        if not isinstance(command, Command):
            raise TypeError('The command passed must be a subclass of Command')

        if isinstance(self, Command):
            command.parent = self

        if command.name in self.all_commands:
            raise ClientException('Command {0.name} is already registered.'.format(command))

        self.all_commands[command.name] = command
        for alias in command.aliases:
            if alias in self.all_commands:
                raise ClientException('The alias {} is already an existing command or alias.'.format(alias))
            self.all_commands[alias] = command

    def remove_command(self, name):
        command = self.all_commands.pop(name, None)

        if command is None:
            return None

        if name in command.aliases:
            return command

        for alias in command.aliases:
            self.all_commands.pop(alias, None)
        return command

    def walk_commands(self):
        for command in tuple(self.all_commands.values()):
            yield command
            if isinstance(command, GroupMixin):
                yield from command.walk_commands()

    def get_command(self, name):
        if ' ' not in name:
            return self.all_commands.get(name)

        names = name.split()
        obj = self.all_commands.get(names[0])
        if not isinstance(obj, GroupMixin):
            return obj

        for name in names[1:]:
            try:
                obj = obj.all_commands[name]
            except (AttributeError, KeyError):
                return None

        return obj

    def command(self, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator


def command(name=None, cls=None, **attrs):
    if cls is None:
        cls = Command

    def decorator(func):
        if isinstance(func, Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)

    return decorator


class _CaseInsensitiveDict(dict):
    def __contains__(self, k):
        return super().__contains__(k.lower())

    def __delitem__(self, k):
        return super().__delitem__(k.lower())

    def __getitem__(self, k):
        return super().__getitem__(k.lower())

    def get(self, k, default=None):
        return super().get(k.lower(), default)

    def pop(self, k, default=None):
        return super().pop(k.lower(), default)

    def __setitem__(self, k, v):
        super().__setitem__(k.lower(), v)


class Command(_BaseCommand):

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self.__original_kwargs__ = kwargs.copy()
        return self

    def __init__(self, func, **kwargs):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Callback must be a coroutine')

        self.name = name = kwargs.get('name') or func.__name__
        if not isinstance(name, str):
            raise TypeError('Name of a command must be a string')

        self.callback = func
        self.enabled = kwargs.get('enabled', True)

        help_doc = kwargs.get('help')
        if help_doc is not None:
            help_doc = inspect.cleandoc(help_doc)
        else:
            help_doc = inspect.getdoc(func)
            if isinstance(help_doc, bytes):
                help_doc = help_doc.decode('utf-8')

        self.help = help_doc

        self.brief = kwargs.get('brief')
        self.usage = kwargs.get('usage')
        self.rest_is_raw = kwargs.get('rest_is_raw', False)
        self.aliases = kwargs.get('aliases', [])

        if not isinstance(self.aliases, (list, tuple)):
            raise TypeError("Aliases of a command must be a list of strings")

        self.description = inspect.cleandoc(kwargs.get('description', ''))
        self.hidden = kwargs.get('hidden', False)

        try:
            cooldown = func.__commands_cooldown__
        except AttributeError:
            cooldown = kwargs.get('cooldown')
        finally:
            self._buckets = CooldownMapping(cooldown)

        self.cooldown_after_parsing = kwargs.get('cooldown_after_parsing', False)
        self.cog = None

        parent = kwargs.get('parent')
        self.parent = parent if isinstance(parent, _BaseCommand) else None
        self._before_invoke = None
        self._after_invoke = None

        try:
            self.checks = func.__commands_checks__
            self.checks.reverse()
        except AttributeError:
            self.checks = kwargs.get('checks', [])
        self.ignore_extra = kwargs.get('ignore_extra', True)

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, function):
        self._callback = function
        self.module = function.__module__

        signature = inspect.signature(function)
        self.params = signature.parameters.copy()

        for key, value in self.params.items():
            if isinstance(value.annotation, str):
                self.params[key] = value = value.replace(annotation=eval(value.annotation, function.__globals__))

    def update(self, **kwargs):
        self.__init__(self.callback, **dict(self.__original_kwargs__, **kwargs))

    def _ensure_assignment_on_copy(self, other):
        other._before_invoke = self._before_invoke
        other._after_invoke = self._after_invoke
        if self.checks != other.checks:
            other.checks = self.checks.copy()
        try:
            other.on_error = self.on_error
        except AttributeError:
            pass
        return other

    def copy(self):
        ret = self.__class__(self.callback, **self.__original_kwargs__)
        return self._ensure_assignment_on_copy(ret)

    def _update_copy(self, kwargs):
        if kwargs:
            kw = kwargs.copy()
            kw.update(self.__original_kwargs__)
            copy = self.__class__(self.callback, **kw)
            return self._ensure_assignment_on_copy(copy)
        else:
            return self.copy()

    async def dispatch_error(self, ctx, error):
        ctx.command_failed = True
        cog = self.cog
        try:
            coro = self.on_error
        except AttributeError:
            pass
        else:
            injected = wrap_callback(coro)
            if cog is not None:
                await injected(cog, ctx, error)
            else:
                await injected(ctx, error)
        try:
            if cog is not None:
                local = Cog._get_overridden_method(cog.cog_command_error)
                if local is not None:
                    wrapped = wrap_callback(local)
                    await wrapped(ctx, error)
        finally:
            ctx.bot.dispatch('command_error', ctx, error)

    async def _actual_conversion(self, ctx, converter, argument, param):
        if converter is bool:
            return converters._convert_to_bool(argument)

        try:
            module = converter.__module__
        except AttributeError:
            pass
        else:
            if module is not None and (module.startswith('vk_botting.') and not module.endswith('converter')):
                converter = getattr(converters, converter.__name__ + 'Converter')

        try:
            if inspect.isclass(converter):
                if issubclass(converter, converters.Converter):
                    instance = converter()
                    ret = await instance.convert(ctx, argument)
                    return ret
                else:
                    method = getattr(converter, 'convert', None)
                    if method is not None and inspect.ismethod(method):
                        ret = await method(ctx, argument)
                        return ret
            elif isinstance(converter, converters.Converter):
                ret = await converter.convert(ctx, argument)
                return ret
        except CommandError:
            raise
        except Exception as exc:
            raise ConversionError(converter, exc) from exc

        try:
            return converter(argument)
        except CommandError:
            raise
        except Exception as exc:
            try:
                name = converter.__name__
            except AttributeError:
                name = converter.__class__.__name__

            raise BadArgument('Converting to "{}" failed for parameter "{}".'.format(name, param.name)) from exc

    async def do_conversion(self, ctx, converter, argument, param):
        try:
            origin = converter.__origin__
        except AttributeError:
            pass
        else:
            if origin is typing.Union:
                errors = []
                _NoneType = type(None)
                for conv in converter.__args__:
                    if conv is _NoneType and param.kind != param.VAR_POSITIONAL:
                        ctx.view.undo()
                        return None if param.default is param.empty else param.default

                    try:
                        value = await self._actual_conversion(ctx, conv, argument, param)
                    except CommandError as exc:
                        errors.append(exc)
                    else:
                        return value

                raise BadUnionArgument(param, converter.__args__, errors)

        return await self._actual_conversion(ctx, converter, argument, param)

    def _get_converter(self, param):
        converter = param.annotation
        if converter is param.empty:
            if param.default is not param.empty:
                converter = str if param.default is None else type(param.default)
            else:
                converter = str
        return converter

    async def transform(self, ctx, param):
        required = param.default is param.empty
        converter = self._get_converter(param)
        consume_rest_is_special = param.kind == param.KEYWORD_ONLY and not self.rest_is_raw
        view = ctx.view
        view.skip_ws()

        if type(converter) is converters._Greedy:
            if param.kind == param.POSITIONAL_OR_KEYWORD:
                return await self._transform_greedy_pos(ctx, param, required, converter.converter)
            elif param.kind == param.VAR_POSITIONAL:
                return await self._transform_greedy_var_pos(ctx, param, converter.converter)
            else:
                converter = converter.converter

        if view.eof:
            if param.kind == param.VAR_POSITIONAL:
                raise RuntimeError()  # break the loop
            if required:
                if self._is_typing_optional(param.annotation):
                    return None
                raise MissingRequiredArgument(param)
            return param.default

        previous = view.index
        if consume_rest_is_special:
            argument = view.read_rest().strip()
        else:
            argument = view.get_quoted_word()
        view.previous = previous

        return await self.do_conversion(ctx, converter, argument, param)

    async def _transform_greedy_pos(self, ctx, param, required, converter):
        view = ctx.view
        result = []
        while not view.eof:
            previous = view.index

            view.skip_ws()
            argument = view.get_quoted_word()
            try:
                value = await self.do_conversion(ctx, converter, argument, param)
            except CommandError:
                view.index = previous
                break
            else:
                result.append(value)

        if not result and not required:
            return param.default
        return result

    async def _transform_greedy_var_pos(self, ctx, param, converter):
        view = ctx.view
        previous = view.index
        argument = view.get_quoted_word()
        try:
            value = await self.do_conversion(ctx, converter, argument, param)
        except CommandError:
            view.index = previous
            raise RuntimeError() from None
        else:
            return value

    @property
    def clean_params(self):
        result = self.params.copy()
        if self.cog is not None:
            result.popitem(last=False)

        try:
            result.popitem(last=False)
        except Exception:
            raise ValueError('Missing context parameter') from None

        return result

    @property
    def full_parent_name(self):
        entries = []
        command = self
        while command.parent is not None:
            command = command.parent
            entries.append(command.name)

        return ' '.join(reversed(entries))

    @property
    def parents(self):
        entries = []
        command = self
        while command.parent is not None:
            command = command.parent
            entries.append(command)

        return entries

    @property
    def root_parent(self):
        if not self.parent:
            return None
        return self.parents[-1]

    @property
    def qualified_name(self):
        parent = self.full_parent_name
        if parent:
            return parent + ' ' + self.name
        else:
            return self.name

    def __str__(self):
        return self.qualified_name

    async def _parse_arguments(self, ctx):
        ctx.args = [ctx] if self.cog is None else [self.cog, ctx]
        ctx.kwargs = {}
        args = ctx.args
        kwargs = ctx.kwargs

        view = ctx.view
        iterator = iter(self.params.items())

        if self.cog is not None:
            try:
                next(iterator)
            except StopIteration:
                fmt = 'Callback for {0.name} command is missing "self" parameter.'
                raise ClientException(fmt.format(self))

        try:
            next(iterator)
        except StopIteration:
            fmt = 'Callback for {0.name} command is missing "ctx" parameter.'
            raise ClientException(fmt.format(self))

        for name, param in iterator:
            if param.kind == param.POSITIONAL_OR_KEYWORD:
                transformed = await self.transform(ctx, param)
                args.append(transformed)
            elif param.kind == param.KEYWORD_ONLY:
                if self.rest_is_raw:
                    converter = self._get_converter(param)
                    argument = view.read_rest()
                    kwargs[name] = await self.do_conversion(ctx, converter, argument, param)
                else:
                    kwargs[name] = await self.transform(ctx, param)
                break
            elif param.kind == param.VAR_POSITIONAL:
                while not view.eof:
                    try:
                        transformed = await self.transform(ctx, param)
                        args.append(transformed)
                    except RuntimeError:
                        break

        if not self.ignore_extra:
            if not view.eof:
                raise TooManyArguments('Too many arguments passed to ' + self.qualified_name)

    async def _verify_checks(self, ctx):
        if not self.enabled:
            raise DisabledCommand('{0.name} command is disabled'.format(self))

        if not await self.can_run(ctx):
            raise CheckFailure('The check functions for command {0.qualified_name} failed.'.format(self))

    async def call_before_hooks(self, ctx):
        cog = self.cog
        if self._before_invoke is not None:
            if cog is None:
                await self._before_invoke(ctx)
            else:
                await self._before_invoke(cog, ctx)

        if cog is not None:
            hook = Cog._get_overridden_method(cog.cog_before_invoke)
            if hook is not None:
                await hook(ctx)

        hook = ctx.bot._before_invoke
        if hook is not None:
            await hook(ctx)

    async def call_after_hooks(self, ctx):
        cog = self.cog
        if self._after_invoke is not None:
            if cog is None:
                await self._after_invoke(ctx)
            else:
                await self._after_invoke(cog, ctx)

        if cog is not None:
            hook = Cog._get_overridden_method(cog.cog_after_invoke)
            if hook is not None:
                await hook(ctx)

        hook = ctx.bot._after_invoke
        if hook is not None:
            await hook(ctx)

    def _prepare_cooldowns(self, ctx):
        if self._buckets.valid:
            current = ctx.message.created_at.replace(tzinfo=datetime.timezone.utc).timestamp()
            bucket = self._buckets.get_bucket(ctx.message, current)
            retry_after = bucket.update_rate_limit(current)
            if retry_after:
                raise CommandOnCooldown(bucket, retry_after)

    async def prepare(self, ctx):
        ctx.command = self
        await self._verify_checks(ctx)

        if self.cooldown_after_parsing:
            await self._parse_arguments(ctx)
            self._prepare_cooldowns(ctx)
        else:
            self._prepare_cooldowns(ctx)
            await self._parse_arguments(ctx)

        await self.call_before_hooks(ctx)

    def is_on_cooldown(self, ctx):
        if not self._buckets.valid:
            return False

        bucket = self._buckets.get_bucket(ctx.message)
        return bucket.get_tokens() == 0

    def reset_cooldown(self, ctx):
        if self._buckets.valid:
            bucket = self._buckets.get_bucket(ctx.message)
            bucket.reset()

    async def invoke(self, ctx):
        await self.prepare(ctx)
        ctx.invoked_subcommand = None
        injected = hooked_wrapped_callback(self, ctx, self.callback)
        await injected(*ctx.args, **ctx.kwargs)

    async def reinvoke(self, ctx, *, call_hooks=False):
        ctx.command = self
        await self._parse_arguments(ctx)

        if call_hooks:
            await self.call_before_hooks(ctx)

        ctx.invoked_subcommand = None
        try:
            await self.callback(*ctx.args, **ctx.kwargs)
        except:
            ctx.command_failed = True
            raise
        finally:
            if call_hooks:
                await self.call_after_hooks(ctx)

    def error(self, coro):
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The error handler must be a coroutine.')

        self.on_error = coro
        return coro

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

    @property
    def cog_name(self):
        return type(self.cog).__cog_name__ if self.cog is not None else None

    @property
    def short_doc(self):
        if self.brief is not None:
            return self.brief
        if self.help is not None:
            return self.help.split('\n', 1)[0]
        return ''

    def _is_typing_optional(self, annotation):
        try:
            origin = annotation.__origin__
        except AttributeError:
            return False

        if origin is not typing.Union:
            return False

        return annotation.__args__[-1] is type(None)

    @property
    def signature(self):
        if self.usage is not None:
            return self.usage

        params = self.clean_params
        if not params:
            return ''

        result = []
        for name, param in params.items():
            greedy = isinstance(param.annotation, converters._Greedy)

            if param.default is not param.empty:
                should_print = param.default if isinstance(param.default, str) else param.default is not None
                if should_print:
                    result.append('[%s=%s]' % (name, param.default) if not greedy else
                                  '[%s=%s]...' % (name, param.default))
                    continue
                else:
                    result.append('[%s]' % name)

            elif param.kind == param.VAR_POSITIONAL:
                result.append('[%s...]' % name)
            elif greedy:
                result.append('[%s]...' % name)
            elif self._is_typing_optional(param.annotation):
                result.append('[%s]' % name)
            else:
                result.append('<%s>' % name)

        return ' '.join(result)

    async def can_run(self, ctx):

        original = ctx.command
        ctx.command = self

        try:
            if not await ctx.bot.can_run(ctx):
                raise CheckFailure('The global check functions for command {0.qualified_name} failed.'.format(self))

            cog = self.cog
            if cog is not None:
                local_check = Cog._get_overridden_method(cog.cog_check)
                if local_check is not None:
                    ret = await maybe_coroutine(local_check, ctx)
                    if not ret:
                        return False

            predicates = self.checks
            if not predicates:
                return True

            return await async_all(predicate(ctx) for predicate in predicates)
        finally:
            ctx.command = original
