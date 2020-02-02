"""
The MIT License (MIT)

Copyright (c) 2019-2020 MrDandycorn

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

from random import choice
import aiohttp
import asyncio

from vk_botting.exceptions import LoginError


class VKClient:

    def __init__(self, user_agent, client_secret, client_id):
        self.user_agent = user_agent
        self.client_secret = client_secret
        self.client_id = client_id


def generate_random_string(length, chars):
    res = ''
    for _ in range(length):
        res += choice(chars)
    return res


class TokenReceiverOfficial:

    def __init__(self, login, password, auth_code='', scope='all'):
        self.login = login
        self.password = password
        self.auth_code = auth_code
        self.scope = scope
        VKOfficial = VKClient("VKAndroidApp/5.23-2978 (Android 4.4.2; SDK 19; x86; unknown Android SDK built for x86; en; 320x240)", "hHbZxrka2uZ6jB1inYsH", "2274003")
        self.client = VKOfficial

    def get_two_factor_part(self):
        if self.auth_code == 'GET_CODE':
            return {'2fa_supported': 1,
                    'force_sms': 1}
        if self.auth_code:
            return {'code': self.auth_code}
        return {'2fa_supported': 1}

    def get_token(self):
        return self.get_non_refreshed()
    
    def get_non_refreshed(self):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._get_non_refreshed())

    async def _get_non_refreshed(self, captcha_sid=None, captcha_key=None):
        device_id = generate_random_string(16, '0123456789abcdef')
        url = 'https://oauth.vk.com/token?grant_type=password'
        headers = {
            'User-Agent': self.client.user_agent
        }
        params = {
            'client_id': self.client.client_id,
            'client_secret': self.client.client_secret,
            'username': self.login,
            'password': self.password,
            'v': '5.93',
            'scope': self.scope,
            'lang': 'en',
            'devide_id': device_id
        }
        if captcha_sid:
            params['captcha_sid'] = captcha_sid
        if captcha_key:
            params['captcha_key'] = captcha_key
        params.update(self.get_two_factor_part())
        async with aiohttp.ClientSession() as client:
            res = await client.post(url, data=params, headers=headers)
            res = await res.json()
        if 'error' in res.keys():
            if res['error'] == 'need_validation':
                if self.auth_code == 'GET_CODE':
                    self.auth_code = input('Input sms code: ')
                    return await self._get_non_refreshed()
                self.auth_code = 'GET_CODE'
                return await self._get_non_refreshed()
            if res['error'] == 'need_captcha':
                key = input(f'Captcha needed ({res["captcha_img"]}): ')
                return await self._get_non_refreshed(res['captcha_sid'], key)
            raise LoginError(res.get('error_description'))
        return res['access_token']


class TokenReceiverKate:

    def __init__(self, login, password, gms_id=4290499058362927820, gms_token=2266394020780474269, auth_code='', scope='audio,offline'):
        self.login = login
        self.password = password
        self.gms_id = gms_id
        self.gms_token = gms_token
        self.auth_code = auth_code
        self.scope = scope
        self.client = VKClient("KateMobileAndroid/52.1 lite-445 (Android 4.4.2; SDK 19; x86; unknown Android SDK built for x86; en)", "lxhD8OD7dMsqtXIm5IUY", "2685278")

    def get_two_factor_part(self):
        if self.auth_code == 'GET_CODE':
            return {'2fa_supported': 1,
                    'force_sms': 1}
        if self.auth_code:
            return {'code': self.auth_code}
        return {'2fa_supported': 1}
        
    def get_token(self):
        token = self.get_non_refreshed()
        receipt = self.get_receipt()
        return self.refresh_token(token, receipt)
    
    def get_non_refreshed(self):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._get_non_refreshed())

    async def _get_non_refreshed(self, captcha_sid=None, captcha_key=None):
        device_id = generate_random_string(16, '0123456789abcdef')
        url = 'https://oauth.vk.com/token?grant_type=password'
        headers = {
            'User-Agent': self.client.user_agent
        }
        params = {
            'client_id': self.client.client_id,
            'client_secret': self.client.client_secret,
            'username': self.login,
            'password': self.password,
            'v': '5.78',
            'scope': self.scope,
            'lang': 'en',
            'devide_id': device_id
        }
        if captcha_sid:
            params['captcha_sid'] = captcha_sid
        if captcha_key:
            params['captcha_key'] = captcha_key
        params.update(self.get_two_factor_part())
        async with aiohttp.ClientSession() as client:
            res = await client.post(url, data=params, headers=headers)
            res = await res.json()
        if 'error' in res.keys():
            if res['error'] == 'need_validation':
                if self.auth_code == 'GET_CODE':
                    self.auth_code = input('Input sms code: ')
                    return await self._get_non_refreshed()
                self.auth_code = 'GET_CODE'
                return await self._get_non_refreshed()
            if res['error'] == 'need_captcha':
                key = input(f'Captcha needed ({res["captcha_img"]}): ')
                return await self._get_non_refreshed(res['captcha_sid'], key)
            raise LoginError(res.get('error_description'))
        self.id = res['user_id']
        return res['access_token']
    
    def refresh_token(self, token, receipt):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._refresh_token(token, receipt))

    async def _refresh_token(self, token, receipt):
        headers = {
            'User-Agent': self.client.user_agent
        }
        params = {
            'access_token': token,
            'receipt': receipt,
            'v': '5.78'
        }
        async with aiohttp.ClientSession() as client:
            res = await client.get('https://api.vk.com/method/auth.refreshToken', params=params, headers=headers)
            res = await res.json()
        new_token = res['response']['token']
        if new_token == token:
            raise LoginError('Token not refreshed. Try using own gms credentials')
        return new_token
    
    def get_receipt(self):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._get_receipt())

    async def _get_receipt(self):
        url = 'https://android.clients.google.com/c2dm/register3'
        headers = {
            'User-Agent': 'Android-GCM/1.5 (generic_x86 KK)',
            'Authorization': f'AidLogin {self.gms_id}:{self.gms_token}'
        }
        params = {
            "X-scope": "GCM",
            "X-osv": "23",
            "X-subtype": "54740537194",
            "X-app_ver": "445",
            "X-kid": "|ID|1|",
            "X-appid": generate_random_string(11, '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-'),
            "X-gmsv": "13283005",
            "X-cliv": "iid-10084000",
            "X-app_ver_name": "52.1 lite",
            "X-X-kid": "|ID|1|",
            "X-subscription": "54740537194",
            "X-X-subscription": "54740537194",
            "X-X-subtype": "54740537194",
            "app": "com.perm.kate_new_6",
            "sender": "54740537194",
            "device": self.gms_id,
            "cert": "966882ba564c2619d55d0a9afd4327a38c327456",
            "app_ver": "445",
            "info": "w8LuNo60zr8UUO6eTSP7b7U4vzObdhY",
            "gcm_ver": "13283005",
            "plat": "0",
            "X-messenger2": "1"
        }
        async with aiohttp.ClientSession() as client:
            await client.post(url, data=params, headers=headers)
            params['X-scope'] = f'id{self.id}'
            params['X-kid'] = params['X-X-kid'] = '|ID|2|'
            res = await client.post(url, data=params, headers=headers)
            res = await res.text()
        res = res.split('|ID|2|:')[1]
        if res == 'PHONE_REGISTRATION_ERROR':
            raise LoginError('PHONE_REGISTRATION_ERROR')
        return res
