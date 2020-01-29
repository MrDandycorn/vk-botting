.. currentmodule:: vk_botting

API Reference
==============

Bot
-------

.. autoclass:: vk_botting.bot.Bot
    :members:
    :inherited-members:

.. autofunction:: vk_botting.bot.when_mentioned

.. autofunction:: vk_botting.bot.when_mentioned_or

.. autofunction:: vk_botting.bot.when_mentioned_or_pm

.. autofunction:: vk_botting.bot.when_mentioned_or_pm_or

.. _vk_api_context_ref:

Context
-------

.. autoclass:: vk_botting.context.Context
    :members:
    :inherited-members:

.. _vk_api_events:

Event Reference
---------------

This page outlines the different types of events listened by :class:`Bot`.

There are two ways to register an event, the first way is through the use of
:meth:`Bot.listen`. The second way is through subclassing :class:`Bot` and
overriding the specific events. For example: ::

    import vk_botting

    class MyBot(vk_botting.Bot):
        async def on_message_new(self, message):
            if message.from_id == self.group.id:
                return

            if message.text.startswith('$hello'):
                await message.send('Hello World!')


If an event handler raises an exception, :func:`on_error` will be called
to handle it, which defaults to print a traceback and ignoring the exception.

.. warning::

    All the events must be a |coroutine_link|_. If they aren't, then you might get unexpected
    errors. In order to turn a function into a coroutine they must be ``async def``
    functions.

.. function:: on_ready()

    Called when the bot is done preparing the data received from VK. Usually after login is successful
    and the :attr:`Bot.group` and co. are filled up.

.. function:: on_error(event, \*args, \*\*kwargs)

    Usually when an event raises an uncaught exception, a traceback is
    printed to stderr and the exception is ignored. If you want to
    change this behaviour and handle the exception for whatever reason
    yourself, this event can be overridden. Which, when done, will
    suppress the default action of printing the traceback.

    The information of the exception raised and the exception itself can
    be retrieved with a standard call to :func:`sys.exc_info`.

    If you want exception to propagate out of the :class:`Bot` class
    you can define an ``on_error`` handler consisting of a single empty
    :ref:`py:raise`.  Exceptions raised by ``on_error`` will not be
    handled in any way by :class:`Bot`.

    :param event: The name of the event that raised the exception.
    :type event: :class:`str`

    :param args: The positional arguments for the event that raised the
        exception.
    :param kwargs: The keyword arguments for the event that raised the
        exception.

.. function:: on_command_error(ctx, error)

    An error handler that is called when an error is raised
    inside a command either through user input error, check
    failure, or an error in your own code.

    A default one is provided (:meth:`Bot.on_command_error`).

    :param ctx: The invocation context.
    :type ctx: :class:`Context`
    :param error: The error that was raised.
    :type error: :class:`CommandError` derived

.. function:: on_command(ctx)

    An event that is called when a command is found and is about to be invoked.

    This event is called regardless of whether the command itself succeeds via
    error or completes.

    :param ctx: The invocation context.
    :type ctx: :class:`Context`

.. function:: on_command_completion(ctx)

    An event that is called when a command has completed its invocation.

    This event is called only if the command succeeded, i.e. all checks have
    passed and the user input it correctly.

    :param ctx: The invocation context.
    :type ctx: :class:`Context`

.. function:: on_message_new(message)

    Called when bot receives a message.

    :param message: Received message.
    :type message: :class:`message.Message`

.. function:: on_message_reply(message)

    Called when bot replies with a message.

    :param message: Sent message.
    :type message: :class:`message.Message`

.. function:: on_message_edit(message)

    Called when message is edited.

    :param message: Edited message.
    :type message: :class:`message.Message`

.. function:: on_message_typing_state(state)

    Called when typing state is changed (e.g. someone starts typing).

    :param state: New state.
    :type state: :class:`states.State`

.. function:: on_chat_kick_user(message)

    Called when user is kicked from the chat.

    :param message: Message sent when user is kicked.
    :type message: :class:`message.Message`

.. function:: on_chat_invite_user(message)

    Called when user is invited to the chat.

    :param message: Message sent when user is invited.
    :type message: :class:`message.Message`

.. function:: on_chat_invite_user_by_link(message)

    Called when user is invited to the chat by link.

    :param message: Message sent when user is invited.
    :type message: :class:`message.Message`

.. function:: on_chat_photo_update(message)

    Called when chat photo is updated.

    :param message: Message sent when photo is updated.
    :type message: :class:`message.Message`

.. function:: on_chat_photo_remove(message)

    Called when chat photo is removed.

    :param message: Message sent when photo is removed.
    :type message: :class:`message.Message`

.. function:: on_chat_create(message)

    Called when chat is created.

    :param message: Message sent when chat is created.
    :type message: :class:`message.Message`

.. function:: on_chat_title_update(message)

    Called when chat title is updated.

    :param message: Message sent when chat title is updated.
    :type message: :class:`message.Message`

.. function:: on_chat_pin_message(message)

    Called when message is pinned in chat.

    :param message: Message sent when message is pinned in chat.
    :type message: :class:`message.Message`

.. function:: on_chat_unpin_message(message)

    Called when message is unpinned in chat.

    :param message: Message sent when message is unpinned in chat.
    :type message: :class:`message.Message`

.. function:: on_message_allow(user)

    Called when user allows getting messages from bot.

    :param user: User who allowed messages.
    :type user: :class:`user.User`

.. function:: on_message_deny(user)

    Called when user denies getting messages from bot.

    :param user: User who denied messages.
    :type user: :class:`user.User`

.. function:: on_photo_new(photo)

    Called when new photo is uploaded to bot group.

    :param photo: Photo that got uploaded.
    :type photo: :class:`attachments.Photo`

.. function:: on_audio_new(audio)

    Called when new audio is uploaded to bot group.

    :param audio: Audio that got uploaded.
    :type audio: :class:`attachments.Audio`

.. function:: on_video_new(video)

    Called when new video is uploaded to bot group.

    :param video: Video that got uploaded.
    :type video: :class:`attachments.Video`

.. function:: on_photo_comment_new(comment)

    Called when new comment is added to photo.

    :param comment: Comment that got send.
    :type comment: :class:`group.PhotoComment`

.. function:: on_photo_comment_edit(comment)

    Called when comment on photo gets edited.

    :param comment: Comment that got edited.
    :type comment: :class:`group.PhotoComment`

.. function:: on_photo_comment_restore(comment)

    Called when comment on photo is restored.

    :param comment: Comment that got restored.
    :type comment: :class:`group.PhotoComment`

.. function:: on_photo_comment_delete(comment)

    Called when comment on photo is deleted.

    :param comment: Comment that got deleted.
    :type comment: :class:`group.DeletedPhotoComment`

.. function:: on_video_comment_new(comment)

    Called when new comment is added to video.

    :param comment: Comment that got send.
    :type comment: :class:`group.VideoComment`

.. function:: on_video_comment_edit(comment)

    Called when comment on video gets edited.

    :param comment: Comment that got edited.
    :type comment: :class:`group.VideoComment`

.. function:: on_video_comment_restore(comment)

    Called when comment on video is restored.

    :param comment: Comment that got restored.
    :type comment: :class:`group.VideoComment`

.. function:: on_video_comment_delete(comment)

    Called when comment on video is deleted.

    :param comment: Comment that got deleted.
    :type comment: :class:`group.DeletedVideoComment`

.. function:: on_market_comment_new(comment)

    Called when new comment is added to market.

    :param comment: Comment that got send.
    :type comment: :class:`group.MarketComment`

.. function:: on_market_comment_edit(comment)

    Called when comment on market gets edited.

    :param comment: Comment that got edited.
    :type comment: :class:`group.MarketComment`

.. function:: on_market_comment_restore(comment)

    Called when comment on market is restored.

    :param comment: Comment that got restored.
    :type comment: :class:`group.MarketComment`

.. function:: on_market_comment_delete(comment)

    Called when comment on market is deleted.

    :param comment: Comment that got deleted.
    :type comment: :class:`group.DeletedMarketComment`

.. function:: on_board_post_new(comment)

    Called when new post is added to board.

    :param comment: New post on the board.
    :type comment: :class:`group.BoardComment`

.. function:: on_board_post_edit(comment)

    Called when post on board gets edited.

    :param comment: Post that got edited.
    :type comment: :class:`group.BoardComment`

.. function:: on_board_post_restore(comment)

    Called when post on board is restored.

    :param comment: Post that got restored.
    :type comment: :class:`group.BoardComment`

.. function:: on_board_post_delete(comment)

    Called when post on board is deleted.

    :param comment: Post that got deleted.
    :type comment: :class:`group.DeletedBoardComment`

.. function:: on_wall_post_new(post)

    Called when new post in added to wall.

    :param post: Post that got added.
    :type post: :class:`group.Post`

.. function:: on_wall_repost(post)

    Called when wall post is reposted.

    :param post: Post that got reposted.
    :type post: :class:`group.Post`

.. function:: on_wall_reply_new(comment)

    Called when new comment is added to wall.

    :param comment: Comment that got send.
    :type comment: :class:`group.WallComment`

.. function:: on_wall_reply_edit(comment)

    Called when comment on wall gets edited.

    :param comment: Comment that got edited.
    :type comment: :class:`group.WallComment`

.. function:: on_wall_reply_restore(comment)

    Called when comment on wall is restored.

    :param comment: Comment that got restored.
    :type comment: :class:`group.WallComment`

.. function:: on_wall_reply_delete(comment)

    Called when comment on wall is deleted.

    :param comment: Comment that got deleted.
    :type comment: :class:`group.DeletedWallComment`

.. function:: on_group_join(user, join_type)

    Called when user joins bot group.

    :param user: User that joined the group.
    :type user: :class:`user.User`
    :param join_type: User join type. Can be 'join' if user just joined, 'unsure' for events, 'accepted' if user was invited, 'approved' if user join request was approved or 'request' if user requested to join
    :type join_type: :class:`str`

.. function:: on_group_leave(user, self)

    Called when user leaves bot group.

    :param user: User that left the group.
    :type user: :class:`user.User`
    :param self: If user left on their own (True) or was kicked (False).
    :type self: :class:`bool`

.. function:: on_user_block(user)

    Called when user is blocked in bot group.

    :param user: User that was blocked.
    :type user: :class:`user.BlockedUser`

.. function:: on_user_unblock(user)

    Called when user is unblocked in bot group.

    :param user: User that was unblocked.
    :type user: :class:`user.UnblockedUser`

.. function:: on_poll_vote_new(vote)

    Called when new poll vote is received.

    :param vote: New vote.
    :type vote: :class:`group.PollVote`

.. function:: on_group_officers_edit(edit)

    Called when group officers are edited.

    :param edit: New edit.
    :type edit: :class:`group.OfficersEdit`

.. function:: on_unknown(payload)

    Called when unknown event is received.

    :param payload: Json payload of the event.
    :type payload: :class:`dict`


.. _vk_api_abcs:

Abstract Base Classes
-----------------------

An :term:`py:abstract base class` (also known as an ``abc``) is a class that models can inherit
to get their behaviour. The Python implementation of an :doc:`abc <py:library/abc>` is
slightly different in that you can register them at run-time. **Abstract base classes cannot be instantiated**.
They are mainly there for usage with :func:`py:isinstance` and :func:`py:issubclass`\.

This library has a module related to abstract base classes, some of which are actually from the :doc:`abc <py:library/abc>` standard
module, others which are not.


.. autoclass:: vk_botting.abstract.Messageable
    :members:
    :exclude-members: typing

    .. automethod:: vk_botting.abstract.Messageable.typing
        :async-with:

Utility Classes
---------------

Attachment
~~~~~~~~~~

.. autoclass:: vk_botting.attachments.AttachmentType
    :members:

.. autoclass:: vk_botting.attachments.Attachment
    :members:

Keyboard
~~~~~~~~~~

.. autoclass:: vk_botting.keyboard.KeyboardColor
    :members:

.. autoclass:: vk_botting.keyboard.Keyboard
    :members:

.. _vk_api_models:

VK Models
---------------

Models are classes that are received from VK and are not meant to be created by
the user of the library.

.. danger::

    The classes listed below are **not intended to be created by users** and are also
    **read-only**.

    For example, this means that you should not make your own :class:`User` instances
    nor should you modify the :class:`User` instance yourself.


User
~~~~~

.. autoclass:: vk_botting.user.User
    :members:
    :inherited-members:
    :exclude-members: typing

    .. automethod:: typing
        :async-with:


Group
~~~~~

.. autoclass:: vk_botting.group.Group
    :members:


Message
~~~~~~~

.. autoclass:: vk_botting.message.Message
    :members:
    :inherited-members:
    :exclude-members: typing

    .. automethod:: typing
        :async-with:

.. _vk_api_errors:

Exceptions
-----------

.. autoclass:: vk_botting.exceptions.VKException

.. autoclass:: vk_botting.exceptions.VKApiError

.. autoclass:: vk_botting.exceptions.CommandError

.. autoclass:: vk_botting.exceptions.CommandNotFound

.. autoclass:: vk_botting.exceptions.DisabledCommand

.. autoclass:: vk_botting.exceptions.CommandOnCooldown

.. autoclass:: vk_botting.exceptions.CheckFailure

.. autoclass:: vk_botting.exceptions.ClientException

.. autoclass:: vk_botting.exceptions.CommandInvokeError

.. autoclass:: vk_botting.exceptions.ArgumentError

.. autoclass:: vk_botting.exceptions.BadArgument

.. autoclass:: vk_botting.exceptions.BadUnionArgument

.. autoclass:: vk_botting.exceptions.MissingRequiredArgument

.. autoclass:: vk_botting.exceptions.TooManyArguments

.. autoclass:: vk_botting.exceptions.ConversionError

.. autoclass:: vk_botting.exceptions.ExtensionError

.. autoclass:: vk_botting.exceptions.ExtensionAlreadyLoaded

.. autoclass:: vk_botting.exceptions.ExtensionNotLoaded

.. autoclass:: vk_botting.exceptions.NoEntryPointError

.. autoclass:: vk_botting.exceptions.ExtensionFailed

.. autoclass:: vk_botting.exceptions.ExtensionNotFound

.. autoclass:: vk_botting.exceptions.UnexpectedQuoteError

.. autoclass:: vk_botting.exceptions.InvalidEndOfQuotedStringError

.. autoclass:: vk_botting.exceptions.ExpectedClosingQuoteError

.. autoclass:: vk_botting.exceptions.LoginError


Additional Classes
------------------

.. autoclass:: vk_botting.commands.GroupMixin
    :members:
    :inherited-members:

.. autoclass:: vk_botting.commands.GroupCommand
    :members:
    :inherited-members:

.. autoclass:: vk_botting.commands.Command
    :members:
    :inherited-members:

.. autoclass:: vk_botting.client.Client
    :members: