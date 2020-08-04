"""
VK Botting Package
~~~~~~~~~~~~~~~~~~~

A basic package for building async VK bots.

:copyright: (c) 2019-2020 MrDandycorn
:license: MIT, see LICENSE for more details.

"""

__title__ = 'vk_botting'
__author__ = 'MrDandycorn'
__license__ = 'MIT'
__copyright__ = 'Copyright 2019-2020 MrDandycorn'
__version__ = '0.9.3'

from collections import namedtuple
import logging

from vk_botting.bot import Bot, when_mentioned, when_mentioned_or, when_mentioned_or_pm, when_mentioned_or_pm_or, UserBot
from vk_botting.client import UserMessageFlags
from vk_botting.attachments import *
from vk_botting.limiters import *
from vk_botting.commands import *
from vk_botting.keyboard import *
from vk_botting.message import Message, Messageable
from vk_botting.exceptions import *
from vk_botting.auth import TokenReceiverKate, TokenReceiverOfficial

VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')

version_info = VersionInfo(major=0, minor=9, micro=3, releaselevel='development', serial=0)

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
