import aiohttp


async def general_request(url, post=False, **params):
    for param in list(params):
        if params[param] is None:
            params.pop(param)
        elif not isinstance(params[param], (str, int)):
            params[param] = str(params[param])
        elif isinstance(params[param], bool):
            params[param] = str(params[param])
    timeout = aiohttp.ClientTimeout(total=100, connect=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        res = await session.post(url, data=params) if post else await session.get(url, params=params)
        return await res.json()


async def vk_request(method, token, **kwargs):
    return await general_request(f'https://api.vk.com/method/{method}', access_token=token, v='5.999', **kwargs)
