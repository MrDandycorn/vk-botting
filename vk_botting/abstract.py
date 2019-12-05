import abc
from general import vk_request
from context_managers import Typing


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
        res = await vk_request('messages.setActivity', self.bot.token, group_id=self.bot.group.id, type='typing', peer_id=peer_id)
        return res

    def typing(self):
        return Typing(self)
