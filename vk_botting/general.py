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

import aiohttp


def convert_params(params):
    for param in list(params):
        if params[param] is None:
            params.pop(param)
        elif not isinstance(params[param], (str, int)):
            params[param] = str(params[param])
        elif isinstance(params[param], bool):
            params[param] = str(params[param])
    return params


async def general_request(url, post=False, **params):
    params = convert_params(params)
    timeout = aiohttp.ClientTimeout(total=100, connect=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        res = await session.post(url, data=params) if post else await session.get(url, params=params)
        return await res.json()


async def vk_request(method, token, post=False, **kwargs):
    return await general_request(f'https://api.vk.com/method/{method}', post=post, access_token=token, v='5.999', **kwargs)
