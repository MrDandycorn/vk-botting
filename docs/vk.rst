.. currentmodule:: vk-botting

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
