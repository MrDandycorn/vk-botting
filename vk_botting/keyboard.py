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

from enum import Enum

from vk_botting.exceptions import VKApiError
from vk_botting.utils import to_json


class KeyboardColor(Enum):
    """Represents Keyboard colors"""
    PRIMARY = 'primary'         #: Primary color (blue)
    SECONDARY = 'secondary'     #: Secondary color (gray)
    NEGATIVE = 'negative'       #: Negative color (red)
    POSITIVE = 'positive'       #: Positive color (green)


class KeyboardButton(Enum):
    """Represents Keyboard button type"""
    TEXT = "text"           #: Text type (default)
    CALLBACK = "callback"   #: Callback type
    LOCATION = "location"   #: Location type
    VKPAY = "vkpay"         #: VKPay type
    VKAPPS = "open_app"     #: Open App type


class Keyboard(object):
    """Class for easier creation and changing of Bot Keyboards.

    Can be used in :meth:`.Bot.send_message` as it is

    Attributes
    ----------
    one_time: :class:`bool`
        If keyboard is one-time (should disappear after one usage)
    inline: :class:`bool`
        If keyboard should be inline. Restricts keyboard to be only 6x5
    """
    def __init__(self, one_time=False, inline=False):
        self.one_time = one_time
        self.inline = inline
        self.lines = [[]]

        self.keyboard = {
            'one_time': self.one_time,
            'inline': self.inline,
            'buttons': self.lines
        }

    def __str__(self):
        return to_json(self.keyboard)

    @classmethod
    def get_empty_keyboard(cls):
        """Classmethod for getting empty keyboard. Useful when keyboard should be cleared"""
        keyboard = cls()
        keyboard.keyboard['buttons'] = []
        return keyboard

    def _add_button(self, button_type, label, color, payload):
        current_line = self.lines[-1]

        if len(current_line) > 4:
            raise VKApiError('Max 5 buttons on a line')
        color_value = color
        if isinstance(color, KeyboardColor):
            color_value = color_value.value
        current_line.append({
            'color': color_value,
            'action': {
                'type': button_type,
                'payload': payload,
                'label': label,
            }
        })

    def add_button(self, label, color=KeyboardColor.PRIMARY, payload=None):
        """Adds button to current line

        Parameters
        ----------
        label: :class:`str`
            Button label to be displayed
        color: :class:Union[`str`, `KeyboardColor`]
            Button color. Can be value from :class:`.KeyboardColor` enum
        payload: :class:`dict`
            Optional. Should be used for some buttons

        Raises
        ------
        vk_botting.VKApiError
            When there are already too many buttons on one line
        """
        self._add_button(KeyboardButton.TEXT.value, label, color, payload)

    def add_callback_button(self, label, color=KeyboardColor.PRIMARY, payload=None):
        """Adds a callback button (https://vk.com/dev/bots_docs_5) to current line

        Parameters
        ----------
        label: :class:`str`
            Button label to be displayed
        color: :class:Union[`str`, `KeyboardColor`]
            Button color. Can be value from :class:`.KeyboardColor` enum
        payload: :class:`dict`
            Optional. Should be used for some buttons

        Raises
        ------
        vk_botting.VKApiError
            When there are already too many buttons on one line
        """
        if not self.inline:
            raise VKApiError('Cannot add a callback button to non-inline keyboard')
        self._add_button(KeyboardButton.CALLBACK.value, label, color, payload)

    def add_location_button(self, payload=None):
        """Adds location button to current line

        Parameters
        ----------
        payload: :class:`dict`
            Payload for a location button

        Raises
        ------
        vk_botting.VKApiError
            When there are already too many buttons on one line
        """
        current_line = self.lines[-1]
        if len(current_line) != 0:
            raise VKApiError('This type of button takes the entire width of the line')

        if payload is not None and not isinstance(payload, str):
            payload = to_json(payload)

        button_type = KeyboardButton.LOCATION.value

        current_line.append({
            'action': {
                'type': button_type,
                'payload': payload
            }
        })

    def add_vkpay_button(self, _hash, payload=None):
        """Adds button to current line

        Parameters
        ----------
        _hash: :class:`str`
            Hash for a VKPay button
        payload: :class:`dict`
            Payload for a VKPay button

        Raises
        ------
        vk_botting.VKApiError
            When there are already too many buttons on one line
        """
        current_line = self.lines[-1]

        if len(current_line) != 0:
            raise VKApiError('This type of button takes the entire width of the line')

        if payload is not None and not isinstance(payload, str):
            payload = to_json(payload)

        button_type = KeyboardButton.VKPAY.value

        current_line.append({
            'action': {
                'type': button_type,
                'payload': payload,
                'hash': _hash
            }
        })

    def add_vkapps_button(self, app_id, owner_id, label, _hash, payload=None):
        """Adds button to current line

        Parameters
        ----------
        app_id: :class:`int`
            Id of VK App
        owner_id: :class:`int`
            Id of VK App owner
        label: :class:`str`
            Button label to be displayed
        _hash: :class:`str`
            Hash for a VK App button
        payload: :class:`dict`
            Optional. Should be used for some button types

        Raises
        ------
        vk_botting.VKApiError
            When there are already too many buttons on one line
        """
        current_line = self.lines[-1]

        if len(current_line) != 0:
            raise VKApiError('This type of button takes the entire width of the line')

        if payload is not None and not isinstance(payload, str):
            payload = to_json(payload)

        button_type = KeyboardButton.VKAPPS.value

        current_line.append({
            'action': {
                'type': button_type,
                'app_id': app_id,
                'owner_id': owner_id,
                'label': label,
                'payload': payload,
                'hash': _hash
            }
        })

    def add_line(self):
        """Adds new line to the keyboard

        Raises
        ------
        vk_botting.VKApiError
            When there are already too many lines in a keyboard
        """
        if (len(self.lines) > 5 and self.inline) or len(self.lines) > 9:
            num = 6 if self.inline else 10
            raise VKApiError('Max {} lines'.format(num))
        self.lines.append([])
