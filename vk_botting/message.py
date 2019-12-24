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

from random import randint
from datetime import datetime

from vk_botting.user import get_pages
from vk_botting.abstract import Messageable
from vk_botting.general import vk_request
from vk_botting.exceptions import VKApiError
from vk_botting.attachments import get_attachment, get_user_attachments


async def build_msg(msg, bot):
    res = Message(msg)
    if res.attachments:
        for i in range(len(res.attachments)):
            res.attachments[i] = await get_attachment(bot.token, res.attachments[i])
    if res.fwd_messages:
        for i in range(len(res.fwd_messages)):
            res.fwd_messages[i] = await build_msg(res.fwd_messages[i], bot)
    if res.reply_message:
        res.reply_message = await build_msg(res.reply_message, bot)
    res.bot = bot
    return res


async def build_user_msg(msg, bot):
    res = UserMessage(msg)
    if res.attachments:
        res.attachments = await get_user_attachments(bot.token, res.attachments)
    res.bot = bot
    return res


class Message(Messageable):

    async def _get_conversation(self):
        return self.peer_id

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.date = datetime.fromtimestamp(data.get('date', 0))
        self.update_time = data.get('update_time')
        self.peer_id = data.get('peer_id')
        self.from_id = data.get('from_id')
        self.text = data.get('text')
        self.random_id = data.get('random_id')
        self.ref = data.get('ref')
        self.ref_source = data.get('ref_source')
        self.attachments = data.get('attachments')
        self.important = data.get('important')
        self.geo = data.get('geo')
        self.payload = data.get('payload')
        self.keyboard = data.get('keyboard')
        self.fwd_messages = data.get('fwd_messages')
        self.reply_message = data.get('reply_message')
        self.action = data.get('action')

    async def edit(self, message=None, *, attachment=None, keep_forward_messages='true', keep_snippets='true'):
        if self.id == 0:
            raise VKApiError('I honestly don`t know but VK just doesn`t return message_id when message is sent into conversation\nIf you tried to edit message in conversation then this error is expected')
        params = {'group_id': self.bot.group.id, 'peer_id': self.peer_id, 'message': message, 'attachment': attachment, 'message_id': self.id,
                  'keep_forward_messages': keep_forward_messages, 'keep_snippets': keep_snippets}
        res = await vk_request('messages.edit', self.bot.token, **params)
        if 'error' in res.keys():
            raise VKApiError('[{error_code}] {error_msg}'.format(**res['error']))
        return res

    async def reply(self, message=None, *, attachment=None, sticker_id=None, keyboard=None):
        peer_id = await self._get_conversation()
        return await self.bot.send_message(peer_id, message, attachment=attachment, reply_to=self.id, sticker_id=sticker_id, keyboard=keyboard)

    async def get_author(self):
        author = await get_pages(self.bot.token, self.from_id)
        return author[0]


class UserMessage(Messageable):

    async def _get_conversation(self):
        return self.peer_id

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.date = data.get('date')
        self.peer_id = data.get('peer_id')
        self.text = data.get('text')
        self.attachments = data.get('attachments')
        self.important = data.get('important')
        self.payload = data.get('payload')
        self.keyboard = data.get('keyboard')

    async def edit(self, message=None, *, attachment=None, keep_forward_messages='true', keep_snippets='true'):
        params = {'group_id': self.bot.group.id, 'peer_id': self.peer_id, 'message': message, 'attachment': attachment, 'message_id': self.id,
                  'keep_forward_messages': keep_forward_messages, 'keep_snippets': keep_snippets}
        res = await vk_request('messages.edit', self.bot.token, **params)
        if 'error' in res.keys():
            raise VKApiError('[{error_code}] {error_msg}'.format(**res['error']))
        return res

    async def reply(self, message=None, *, attachment=None, sticker_id=None, keyboard=None):
        peer_id = await self._get_conversation()
        params = {'group_id': self.bot.group.id, 'random_id': randint(-2 ** 63, 2 ** 63 - 1), 'peer_id': peer_id, 'message': message, 'attachment': attachment,
                  'reply_to': self.id, 'sticker_id': sticker_id, 'keyboard': keyboard}
        res = await vk_request('messages.send', self.bot.token, **params)
        if 'error' in res.keys():
            raise VKApiError('[{error_code}] {error_msg}'.format(**res['error']))
        params['id'] = res['response']
        return await build_msg(params, self.bot)

    async def get_author(self):
        user = await get_pages(self.bot.token, self.from_id)
        if user:
            return user[0]
        return None
