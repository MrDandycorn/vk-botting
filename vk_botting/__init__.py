"""
VK Botting Package
~~~~~~~~~~~~~~~~~~~

A basic package for building async VK bots.

:copyright: Original work (c) 2015-present Rapptz
:copyright: Modified work (c) 2019-present MrDandycorn
:license: MIT, see LICENSE for more details.

"""

__title__ = 'vk_botting'
__author__ = 'MrDandycorn'
__license__ = 'MIT'
__copyright__ = 'Copyright 2019-present MrDandycorn'
__version__ = '0.11.0'

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

VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')

version_info = VersionInfo(major=0, minor=11, micro=0, releaselevel='development', serial=0)

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
