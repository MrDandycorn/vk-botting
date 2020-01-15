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

import abc

from vk_botting.context_managers import Typing


class Messageable(metaclass=abc.ABCMeta):
    __slots__ = ()

    @abc.abstractmethod
    async def _get_conversation(self):
        raise NotImplementedError

    async def send(self, message=None, *, attachment=None, sticker_id=None, keyboard=None, reply_to=None, forward_messages=None):
        peer_id = await self._get_conversation()
        return await self.bot.send_message(peer_id, message, attachment=attachment, sticker_id=sticker_id, keyboard=keyboard, reply_to=reply_to, forward_messages=forward_messages)

    async def trigger_typing(self):
        peer_id = await self._get_conversation()
        res = await self.bot.vk_request('messages.setActivity', group_id=self.bot.group.id, type='typing', peer_id=peer_id)
        return res

    def typing(self):
        return Typing(self)
