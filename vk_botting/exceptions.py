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


def flatten_error_dict(d, key=''):
    items = []
    for k, v in d.items():
        new_key = key + '.' + k if key else k

        if isinstance(v, dict):
            try:
                _errors = v['_errors']
            except KeyError:
                items.extend(flatten_error_dict(v, new_key).items())
            else:
                items.append((new_key, ' '.join(x.get('message', '') for x in _errors)))
        else:
            items.append((new_key, v))

    return dict(items)


class VKException(Exception):
    pass


class VKApiError(VKException):
    pass


class CommandError(VKException):
    def __init__(self, message=None, *args):
        if message is not None:
            super().__init__(message, *args)
        else:
            super().__init__(*args)


class CommandNotFound(VKException):
    pass


class DisabledCommand(CommandError):
    pass


class CommandOnCooldown(CommandError):
    pass


class CheckFailure(CommandError):
    pass


class ClientException(VKException):
    pass


class CommandInvokeError(CommandError):
    def __init__(self, e):
        self.original = e
        super().__init__('Command raised an exception: {0.__class__.__name__}: {0}'.format(e))


class ArgumentError(VKException):
    pass


class BadArgument(ArgumentError):
    pass


class BadUnionArgument(BadArgument):
    pass


class MissingRequiredArgument(VKException):
    pass


class TooManyArguments(VKException):
    pass


class ConversionError(VKException):
    pass


class ExtensionError(VKException):
    def __init__(self, message=None, *args, name):
        self.name = name
        m = message or 'Extension {!r} had an error.'.format(name)
        super().__init__(m, *args)


class ExtensionAlreadyLoaded(ExtensionError):
    def __init__(self, name):
        super().__init__('Extension {!r} is already loaded.'.format(name), name=name)


class ExtensionNotLoaded(ExtensionError):
    def __init__(self, name):
        super().__init__('Extension {!r} has not been loaded.'.format(name), name=name)


class NoEntryPointError(ExtensionError):
    def __init__(self, name):
        super().__init__("Extension {!r} has no 'setup' function.".format(name), name=name)


class ExtensionFailed(ExtensionError):
    def __init__(self, name, original):
        self.original = original
        fmt = 'Extension {0!r} raised an error: {1.__class__.__name__}: {1}'
        super().__init__(fmt.format(name, original), name=name)


class ExtensionNotFound(ExtensionError):
    def __init__(self, name, original):
        self.original = original
        fmt = 'Extension {0!r} could not be loaded.'
        super().__init__(fmt.format(name), name=name)


class UnexpectedQuoteError(ArgumentError):
    def __init__(self, quote):
        self.quote = quote
        super().__init__('Unexpected quote mark, {0!r}, in non-quoted string'.format(quote))


class InvalidEndOfQuotedStringError(ArgumentError):
    def __init__(self, char):
        self.char = char
        super().__init__('Expected space after closing quotation but received {0!r}'.format(char))


class ExpectedClosingQuoteError(ArgumentError):
    def __init__(self, close_quote):
        self.close_quote = close_quote
        super().__init__('Expected closing {}.'.format(close_quote))


class HTTPException(VKException):

    def __init__(self, response, message):
        self.response = response
        self.status = response.status
        if isinstance(message, dict):
            self.code = message.get('code', 0)
            base = message.get('message', '')
            errors = message.get('errors')
            if errors:
                errors = flatten_error_dict(errors)
                helpful = '\n'.join('In %s: %s' % t for t in errors.items())
                self.text = base + '\n' + helpful
            else:
                self.text = base
        else:
            self.text = message
            self.code = 0

        fmt = '{0.status} {0.reason} (error code: {1})'
        if len(self.text):
            fmt = fmt + ': {2}'

        super().__init__(fmt.format(self.response, self.code, self.text))


class Forbidden(HTTPException):
    pass


class NotFound(HTTPException):
    pass


class LoginError(VKException):
    pass


class MissingPermissions(VKException):
    def __init__(self, permission):
        self.permission = permission
        super().__init__(f'Missing permission: {self.permission}')
