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

import asyncio


def _typing_done_callback(fut):
    try:
        fut.exception()
    except (asyncio.CancelledError, Exception):
        pass


class Typing:
    def __init__(self, messageable):
        self.bot = messageable.bot
        self.loop = messageable.bot.loop
        self.messageable = messageable

    async def send_typing(self, peer_id):
        await self.bot.vk_request('messages.setActivity', group_id=self.bot.group.id, type='typing', peer_id=peer_id)

    async def do_typing(self):
        try:
            conversation = self._conversation
        except AttributeError:
            conversation = self._conversation = await self.messageable._get_conversation()

        while True:
            await self.send_typing(conversation)
            await asyncio.sleep(5)

    def __enter__(self):
        self.task = asyncio.ensure_future(self.do_typing(), loop=self.loop)
        self.task.add_done_callback(_typing_done_callback)
        return self

    def __exit__(self, exc_type, exc, tb):
        self.task.cancel()

    async def __aenter__(self):
        self._conversation = conversation = await self.messageable._get_conversation()
        await self.send_typing(conversation)
        return self.__enter__()

    async def __aexit__(self, exc_type, exc, tb):
        self.task.cancel()
