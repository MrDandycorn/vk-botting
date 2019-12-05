from inspect import isawaitable
import json
import datetime
from email.utils import parsedate_to_datetime


async def async_all(gen, *, check=isawaitable):
    for elem in gen:
        if check(elem):
            elem = await elem
        if not elem:
            return False
    return True


async def maybe_coroutine(f, *args, **kwargs):
    value = f(*args, **kwargs)
    if isawaitable(value):
        return await value
    else:
        return value


def find(predicate, seq):
    for element in seq:
        if predicate(element):
            return element
    return None


def to_json(obj):
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=True)
