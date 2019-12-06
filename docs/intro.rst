.. currentmodule:: vk-botting

.. _intro:

Introduction
==============

This is the documentation for vk-botting, a library for Python to aid
in creating applications that utilise the VK API.

Prerequisites
---------------

vk-botting works with Python 3.6.0 or higher. Support for earlier versions of Python
is not provided. Python 2.7 or lower is not supported.


.. _installing:

Installing
-----------

You can get the library directly from PyPI: ::

    python3 -m pip install -U vk-botting

If you are using Windows, then the following should be used instead: ::

    py -3 -m pip install -U vk-botting

Virtual Environments
~~~~~~~~~~~~~~~~~~~~~

Sometimes you want to keep libraries from polluting system installs or use a different version of
libraries than the ones installed on the system. You might also not have permissions to install libaries system-wide.
For this purpose, the standard library as of Python 3.3 comes with a concept called "Virtual Environment"s to
help maintain these separate versions.

A more in-depth tutorial is found on `Virtual Environments and Packages <https://docs.python.org/3/tutorial/venv.html>`_.

However, for the quick and dirty:

1. Go to your project's working directory:

    .. code-block:: shell

        $ cd your-bot-source
        $ python3 -m venv bot-env

2. Activate the virtual environment:

    .. code-block:: shell

        $ source bot-env/bin/activate

    On Windows you activate it with:

    .. code-block:: shell

        $ bot-env\Scripts\activate.bat

3. Use pip like usual:

    .. code-block:: shell

        $ pip install -U vk-botting

Congratulations. You now have a virtual environment all set up.

Basic Concepts
---------------

vk-botting revolves around the concept of :ref:`events <vk-api-events>`.
An event is something you listen to and then respond to. For example, when a message
happens, you will receive an event about it that you can respond to.

A quick example to showcase how events work:

.. code-block:: python3

    import vk_botting


    class MyBot(vk_botting.Bot):
        async def on_ready(self):
            print(f'Logged on as {self.group.name}!')

        async def on_message_new(self, message):
            author = await message.get_author()
            print(f'Message from {author.first_name}: {message.text}')


    bot = MyBot('your-prefix-here')
    bot.run('your-token-here')
