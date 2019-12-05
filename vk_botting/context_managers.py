import asyncio

from vk_botting.general import vk_request


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
        await vk_request('messages.setActivity', self.bot.token, group_id=self.bot.group.id, type='typing', peer_id=peer_id)

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
