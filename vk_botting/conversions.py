from vk_botting.exceptions import BadArgument


def _convert_to_bool(argument):
    lowered = argument.lower()
    if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
        return True
    elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
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
