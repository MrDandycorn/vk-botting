from exceptions import NotInUserList
from commands import Command


def check(predicate):

    def decorator(func):
        if isinstance(func, Command):
            func.checks.append(predicate)
        else:
            if not hasattr(func, '__commands_checks__'):
                func.__commands_checks__ = []

            func.__commands_checks__.append(predicate)

        return func
    return decorator


def in_user_list(*ids):
    ids = list(map(int, ids))

    def predicate(ctx):
        if ctx.message.from_id in ids:
            return True
        raise NotInUserList(f'{ctx.message.from_id} is not in provided user list')

    return check(predicate)
