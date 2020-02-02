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

import abc

from vk_botting.context_managers import Typing


class Messageable(metaclass=abc.ABCMeta):
    """An ABC that details the common operations on a model that can send messages.

        The following implement this ABC:

        - :class:`.User`
        - :class:`.Message`
        - :class:`.UserMessage`
        - :class:`.Context`
        """
    __slots__ = ()

    @abc.abstractmethod
    async def _get_conversation(self):
        raise NotImplementedError

    async def send(self, message=None, *, attachment=None, sticker_id=None, keyboard=None, reply_to=None, forward_messages=None):
        """|coro|

        Sends a message to the destination with the text given.

        The content must be a type that can convert to a string through ``str(message)``.

        If the content is set to ``None`` (the default), then the ``attachment`` or ``sticker_id`` parameter must
        be provided.

        If the ``attachment`` parameter is provided, it must be :class:`str`, List[:class:`str`], :class:`.Attachment` or List[:class:`.Attachment`]

        If the ``keyboard`` parameter is provided, it must be :class:`str` or :class:`.Keyboard` (recommended)

        Parameters
        ------------
        message: :class:`str`
            The text of the message to send.
        attachment: Union[List[:class:`str`], :class:`str`, List[:class:`.Attachment`], :class:`.Attachment`]
            The attachment to the message sent.
        sticker_id: Union[:class:`str`, :class:`int`]
            Sticker_id to be sent.
        keyboard: :class:`.Keyboard`
            The keyboard to send along message.
        reply_to: Union[:class:`str`, :class:`int`]
            A message id to reply to.
        forward_messages: Union[List[:class:`int`], List[:class:`str`]]
            Message ids to be forwarded along with message.

        Raises
        --------
        vk_botting.VKApiError
            When error is returned by VK API.

        Returns
        ---------
        :class:`.Message`
            The message that was sent.
        """
        peer_id = await self._get_conversation()
        return await self.bot.send_message(peer_id, message, attachment=attachment, sticker_id=sticker_id, keyboard=keyboard, reply_to=reply_to, forward_messages=forward_messages)

    async def trigger_typing(self):
        """|coro|

        Triggers typing state of bot.

        Can be used instead of :meth:`.typing` in some cases.

        Typing state ends in 10 seconds or when message is sent.

        Raises
        --------
        vk_botting.VKApiError
            When error is returned by VK API.

        Returns
        ---------
        :class:`dict`
            Json payload result of VK API request.
        """
        peer_id = await self._get_conversation()
        res = await self.bot.vk_request('messages.setActivity', group_id=self.bot.group.id, type='typing', peer_id=peer_id)
        return res

    def typing(self):
        """Returns a context manager that allows you to type for an indefinite period of time.

        This is useful for denoting long computations in your bot.

        .. note::

            This is both a regular context manager and an async context manager.
            This means that both ``with`` and ``async with`` work with this.

        Example Usage: ::

            async with ctx.typing():
                # do expensive stuff here
                await ctx.send('done!')

        """
        return Typing(self)
