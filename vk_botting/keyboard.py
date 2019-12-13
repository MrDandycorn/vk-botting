"""
The MIT License (MIT)

Copyright (c) 2019 MrDandycorn

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

from vk_botting.utils import to_json
from vk_botting.exceptions import VKApiError


class KeyboardColor(Enum):
    PRIMARY = 'primary'
    SECONDARY = 'secondary'
    NEGATIVE = 'negative'
    POSITIVE = 'positive'


class KeyboardButton(Enum):
    TEXT = "text"
    LOCATION = "location"
    VKPAY = "vkpay"
    VKAPPS = "open_app"


class Keyboard(object):
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
        keyboard = cls()
        keyboard.keyboard['buttons'] = []
        return keyboard

    def add_button(self, label, color=KeyboardColor.PRIMARY, payload=None):
        current_line = self.lines[-1]

        if len(current_line) > 4:
            raise VKApiError('Max 5 buttons on a line')
        color_value = color
        if isinstance(color, KeyboardColor):
            color_value = color_value.value
        if payload is not None and not isinstance(payload, str):
            payload = to_json(payload)
        button_type = KeyboardButton.TEXT.value
        current_line.append({
            'color': color_value,
            'action': {
                'type': button_type,
                'payload': payload,
                'label': label,
            }
        })

    def add_location_button(self, payload=None):
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

    def add_vkpay_button(self, hash, payload=None):
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
                'hash': hash
            }
        })

    def add_vkapps_button(self, app_id, owner_id, label, hash, payload=None):
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
                'hash': hash
            }
        })

    def add_line(self):
        if (len(self.lines) > 5 and self.inline) or len(self.lines) > 9:
            num = 6 if self.inline else 10
            raise VKApiError(f'Max {num} lines')
        self.lines.append([])
