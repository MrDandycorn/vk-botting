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

from vk_botting.exceptions import BadArgument


def _convert_to_bool(argument):
    lowered = argument.lower()
    if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on', 'да', 'включить', 'правда'):
        return True
    elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off', 'нет', 'выключить', 'ложь'):
        return False
    else:
        raise BadArgument(lowered + ' is not a recognised boolean option')


class Converter:

    async def convert(self, ctx, argument):
        raise NotImplementedError('Derived classes need to implement this.')


class _Greedy:
    __slots__ = ('converter',)

    def __init__(self, *, converter=None):
        self.converter = converter

    def __getitem__(self, params):
        if not isinstance(params, tuple):
            params = (params,)
        if len(params) != 1:
            raise TypeError('Greedy[...] only takes a single argument')
        converter = params[0]

        if not (callable(converter) or isinstance(converter, Converter) or hasattr(converter, '__origin__')):
            raise TypeError('Greedy[...] expects a type or a Converter instance.')

        if converter is str or converter is type(None) or converter is _Greedy:
            raise TypeError('Greedy[%s] is invalid.' % converter.__name__)

        return self.__class__(converter=converter)
