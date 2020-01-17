.. currentmodule:: vk_botting

.. _vk-intro:

Creating a Bot
========================

In order to work with the library and the VK API in general, we must first create a VK Bot.

Creating a Bot is a pretty straightforward process.

1. Make sure you're logged on to the `VK website <https://vk.com/>`_.
2. Go to the group you are administrator of.
3. Navigate to the Manage -> Messages.
4. Enable "Community messages".
5. Navigate to the Settings -> API usage -> Access tokens.
6. Click on the "Create token" button.
7. Allow everything you see necessary and click on the "Create" button.
8. Confirm the action if prompted.
9. Copy the new access token and store it somewhere safe.

    .. warning::

        It should be worth noting that this token is essentially your bot's
        password. You should **never** share this to someone else. In doing so,
        someone can log in to your bot and do malicious things, such as removing
        wall posts, spamming messages or even banning all members.

        The possibilities are endless, so **do not share this token.**

        If you accidentally leaked your token, click the "Delete token" button as soon
        as possible. This revokes your old token and you can then generate a new one.
        Now you need to use the new token to login.

And that's it. You now have a bot account and you can login with that token.

Enabling Longpoll
========================

For the Bot to be able to catch events, you first have to enable Longpoll.

    .. attention::

        Library can do it automatically if you use :func:`force` parameter

1. Make sure you're logged on to the `VK website <https://vk.com/>`_.
2. Go to the group you are administrator of.
3. Navigate to the Manage -> Settings -> API usage -> Long Poll API.
4. Enable "Long Poll API" and set "API version" to latest possible (highest number after dot).
5. Navigate to the "Event types" tab.
6. Check all of the events you need. If you do not know what to check, check everything.

Now you should be able to use the library.
