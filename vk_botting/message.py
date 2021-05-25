"""
The MIT License (MIT)

Original work Copyright (c) 2015-present Rapptz
Modified work Copyright (c) 2019-present MrDandycorn

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

from copy import deepcopy
from datetime import datetime
from random import randint

from vk_botting.abstract import Messageable
from vk_botting.exceptions import VKApiError


class MessageEvent:
    """Represents a message event (https://vk.com/dev/bots_docs_5).

    Attributes
    ----------
    conversation_message_id: :class:`int`
        Id of the message in conversation
    user_id: :class:`int`
        Id of the user that triggered the event
    peer_id: :class:`int`
        Id of conversation where message was sent
    event_id: :class:`str`
        Unique id of the event (can only be used once within 60 seconds)
    payload: :class:`dict`
        Payload sent along with the button. Can be None
    """
    __slots__ = ('bot', 'conversation_message_id', 'user_id', 'peer_id', 'event_id', 'payload')

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.conversation_message_id = data.get('conversation_message_id')
        self.user_id = data.get('user_id')
        self.peer_id = data.get('peer_id')
        self.event_id = data.get('event_id')
        self.payload = data.get('payload')

    async def _answer(self, event_data):
        res = await self.bot.vk_request('messages.sendMessageEventAnswer', event_id=self.event_id, user_id=self.user_id, peer_id=self.peer_id, event_data=event_data)
        if 'error' in res.keys():
            raise VKApiError('[{error_code}] {error_msg}'.format(**res['error']))
        return res

    async def blank_answer(self):
        """|coro|

        Coroutine to send a blank answer to the event (stops loading animation on the button).

        Raises
        --------
        vk_botting.VKApiError
            When error is returned by VK API.

        Returns
        ---------
        :class:`dict`
            Server answer
        """
        return await self._answer(None)

    async def show_snackbar(self, text):
        """|coro|

        Coroutine to send a show_snackbar answer to the event (shows a snackbar to a user).

        Parameters
        ----------
        text: :class:`str`
            Text to be displayed on a snackbar

        Raises
        --------
        vk_botting.VKApiError
            When error is returned by VK API.

        Returns
        ---------
        :class:`dict`
            Server answer
        """
        return await self._answer({
            'type': 'show_snackbar',
            'text': text,
        })

    async def open_link(self, link):
        """|coro|

        Coroutine to send an open_link answer to the event (opens certain link).

        Parameters
        ----------
        link: :class:`str`
            Link to be opened

        Raises
        --------
        vk_botting.VKApiError
            When error is returned by VK API.

        Returns
        ---------
        :class:`dict`
            Server answer
        """
        return await self._answer({
            'type': 'open_link',
            'link': link,
        })

    async def open_app(self, app_id, owner_id, _hash):
        """|coro|

        Coroutine to send an open_app answer to the event (opens certain VK App).

        Parameters
        ----------
        app_id: :class:`int`
            Id of an app to be opened
        owner_id: :class:`Optional[int]`
            owner_id of said app
        _hash: :class:`str`
            I don't actually know what this one is for (read vk docs)

        Raises
        --------
        vk_botting.VKApiError
            When error is returned by VK API.

        Returns
        ---------
        :class:`dict`
            Server answer
        """
        return await self._answer({
            'type': 'open_app',
            'app_id': app_id,
            'owner_id': owner_id,
            'hash': _hash,
        })


class MessageAction:
    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.type = data.get('type')
        self.member_id = data.get('member_id')
        self.text = data.get('text')
        self.email = data.get('email')
        self.photo = data.get('photo')


class Message(Messageable):
    """Represents any message sent or received by bot.

    Should only be created using :meth:`.Bot.build_msg`

    Attributes
    ----------
    id: :class:`int`
        Id of the message in conversation

        .. warning::

            Do not try to use this parameter in group chats with Bot, as it will always be 0 and cause errors.

    date: :class:`datetime.datetime`
        Datetime when message was sent
    update_time: :class:`datetime.datetime`
        Datetime when message was updated
    peer_id: :class:`int`
        Id of conversation where message was sent
    from_id: :class:`int`
        Id of message author
    text: :class:`str`
        Text of the message. Can be empty
    attachments: List[:class:`.Attachment`]
        List of attachments delivered with message
    fwd_messages: List[:class:`.Message`]
        List of forwarded messages
    reply_message: :class:`.Message`
        Message that this message replied to
    action: Union[:class:`.MessageAction`, :class:`NoneType`]
        Action payload
    """

    async def _get_conversation(self):
        return self.peer_id

    def __init__(self, data):
        self.original_data = deepcopy(data)
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.date = datetime.fromtimestamp(data.get('date', 86400))
        self.update_time = datetime.fromtimestamp(data.get('update_time', 86400))
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
        action = data.get('action')
        self.action = MessageAction(action) if action else None
        self.conversation_message_id = data.get('conversation_message_id')

    async def edit(self, message=None, *, attachment=None, keep_forward_messages=1, keep_snippets=1):
        """|coro|

        Coroutine to edit the message.

        Parameters
        ----------
        message: :class:`str`
            New text of the message.
        attachment: Union[List[:class:`str`], :class:`str`, List[:class:`.Attachment`], :class:`.Attachment`]
            New attachment to the message.
        keep_forward_messages: :class:`bool`
            ``True`` if fwd_messages should be kept. Defaults to ``True``
        keep_snippets: :class:`bool`
            ``True`` if snippets should be kept. Defaults to ``True``

        Raises
        --------
        vk_botting.VKApiError
            When error is returned by VK API.

        Returns
        ---------
        :class:`.Message`
            The message that was sent.
        """
        params = {
            'group_id': self.bot.group.id,
            'peer_id': self.peer_id,
            'message': message,
            'attachment': attachment,
            'keep_forward_messages': keep_forward_messages,
            'keep_snippets': keep_snippets,
            'conversation_message_id': self.conversation_message_id
        }
        res = await self.bot.vk_request('messages.edit', **params)
        if 'error' in res.keys():
            raise VKApiError('[{error_code}] {error_msg}'.format(**res['error']))
        return res

    async def delete(self, delete_for_all=1):
        """|coro|

        Coroutine to delete the message.

        Parameters
        ----------
        delete_for_all: :class:`bool`
            ``True`` if message should be deleted for all users. Defaults to ``True``

        Raises
        --------
        vk_botting.VKApiError
            When error is returned by VK API.
        """
        params = {
            'group_id': self.bot.group.id,
            'delete_for_all': delete_for_all,
            'peer_id': self.peer_id,
            'conversation_message_ids': self.conversation_message_id,
        }
        res = await self.bot.vk_request('messages.delete', **params)
        if 'error' in res.keys():
            raise VKApiError('[{error_code}] {error_msg}'.format(**res['error']))

    async def reply(self, message=None, **kwargs):
        """|coro|

        Sends a message to the destination as a reply to original message.

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

        Raises
        --------
        vk_botting.VKApiError
            When error is returned by VK API.

        Returns
        ---------
        :class:`.Message`
            The message that was sent.
        """
        forward = {
            'peer_id': self.peer_id,
            'is_reply': True,
            'conversation_message_ids': self.conversation_message_id,
        }
        kwargs['forward'] = forward
        return await self.bot.send_message(self.peer_id, message, **kwargs)

    async def get_user(self):
        """|coro|
        Returns the author of original message as instance of :class:`.User` class
        """
        author = await self.bot.get_pages(self.from_id)
        return author[0]

    async def get_author(self):
        """|coro|
        Alternative for :meth:`.Message.get_user`
        """
        return await self.get_user()

    async def fetch_user(self):
        """|coro|
        Alternative for :meth:`.Message.get_user`
        """
        return await self.get_user()

    async def fetch_author(self):
        """|coro|
        Alternative for :meth:`.Message.get_user`
        """
        return await self.get_user()


class UserMessage(Messageable):

    async def _get_conversation(self):
        return self.peer_id

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.date = data.get('date')
        self.flags = data.get('flags')
        self.peer_id = data.get('peer_id')
        self.from_id = data.get('from_id')
        self.text = data.get('text')
        self.attachments = data.get('attachments')
        self.important = data.get('important')
        self.payload = data.get('payload')
        self.keyboard = data.get('keyboard')

    async def edit(self, message=None, *, attachment=None, keep_forward_messages='true', keep_snippets='true'):
        params = {'peer_id': self.peer_id, 'message': message, 'attachment': attachment, 'message_id': self.id,
                  'keep_forward_messages': keep_forward_messages, 'keep_snippets': keep_snippets}
        res = await self.bot.vk_request('messages.edit', **params)
        if 'error' in res.keys():
            raise VKApiError('[{error_code}] {error_msg}'.format(**res['error']))
        return res

    async def reply(self, message=None, *, attachment=None, sticker_id=None, keyboard=None):
        peer_id = await self._get_conversation()
        params = {'random_id': randint(-2 ** 63, 2 ** 63 - 1), 'peer_id': peer_id, 'message': message, 'attachment': attachment,
                  'reply_to': self.id, 'sticker_id': sticker_id, 'keyboard': keyboard}
        res = await self.bot.vk_request('messages.send', **params)
        if 'error' in res.keys():
            raise VKApiError('[{error_code}] {error_msg}'.format(**res['error']))
        params['id'] = res['response']
        return self.bot.build_msg(params)

    async def get_user(self):
        user = await self.bot.get_pages(self.from_id)
        if user:
            return user[0]
        return None

    async def get_author(self):
        return await self.get_user()

    async def fetch_user(self):
        return await self.get_user()

    async def fetch_author(self):
        return await self.get_user()
