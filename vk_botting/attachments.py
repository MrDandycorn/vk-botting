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
from aiohttp import ClientSession
import os


class AttachmentType(Enum):
    """Specifies the type of :class:`.Attachment`"""
    PHOTO = 'photo'     #: Attached photo
    VIDEO = 'video'     #: Attached video
    AUDIO = 'audio'     #: Attached audio
    DOCUMENT = 'doc'    #: Attached document
    WALL = 'wall'       #: Attached wall post
    MARKET = 'market'   #: Attached market good
    POLL = 'poll'       #: Attached poll


class DocType(Enum):
    DOCUMENT = 'doc'
    AUDIO_MESSAGE = 'audio_message'
    GRAFFITI = 'graffiti'


async def upload_document(bot, peer_id, file, type=DocType.DOCUMENT, title=None):
    if isinstance(type, DocType):
        type = type.value
    async with ClientSession() as session:
        r = await bot.vk_request('docs.getMessagesUploadServer', peer_id=peer_id, type=type)
        imurl = r['response']['upload_url']
        files = {'file': open(file, 'rb')}
        r = await session.post(imurl, data=files)
        r = await r.json()
        filedata = r['file']
        if title is None:
            title = os.path.splitext(file)[0]
        r = await bot.vk_request('docs.save', file=filedata, title=title)
        doc = r['response']
        doc = doc[doc['type']]
    return Attachment(doc['owner_id'], doc['id'], AttachmentType.DOCUMENT)


async def upload_photo(bot, peer_id, file):
    async with ClientSession() as session:
        r = await bot.vk_request('photos.getMessagesUploadServer', peer_id=peer_id)
        imurl = r['response']['upload_url']
        files = {'file': open(file, 'rb')}
        r = await session.post(imurl, data=files)
        r = await r.json(content_type='text/html')
        r = await bot.vk_request('photos.saveMessagesPhoto', **r)
        doc = r['response'][0]
    return Attachment(doc['owner_id'], doc['id'], AttachmentType.PHOTO)


async def get_photo(bot, obj):
    photo = Photo(obj)
    photo.author, photo.owner = await bot.get_pages(photo.user_id, photo.owner_id)
    return photo


async def get_video(bot, obj):
    video = Video(obj)
    owner = await bot.get_pages(video.owner_id)
    video.owner = owner[0]
    return video


async def get_audio(bot, obj):
    audio = Audio(obj)
    owner = await bot.get_pages(audio.owner_id)
    audio.owner = owner[0]
    return audio


async def get_attachment(obj):
    t = obj['type']
    if t == 'audio_message':
        return AudioMessage(obj[t])
    elif t == 'photo':
        return Photo(obj[t])
    elif t == 'sticker':
        return Sticker(obj[t])
    elif t == 'video':
        return Video(obj[t])
    elif t == 'audio':
        return Audio(obj[t])
    elif t == 'doc':
        return Document(obj[t])
    elif t == 'poll':
        return Poll(obj[t])
    else:
        return t, obj[t]


async def get_user_attachments(atts):
    res = []
    for i in range(len(atts)//2):
        t = atts.get(f'attach{i}_type')
        att = atts.get(f'attach{i}')
        if not att or t == 'sticker':
            continue
        oid, aid = att.split('_')
        obj = {'owner_id': oid, 'id': aid}
        if t == 'audio_message':
            res.append(AudioMessage(obj))
        elif t == 'photo':
            res.append(Photo(obj))
        elif t == 'sticker':
            res.append(Sticker(obj))
        elif t == 'video':
            res.append(Video(obj))
        elif t == 'audio':
            res.append(Audio(obj))
        elif t == 'doc':
            res.append(Document(obj))
        else:
            res.append(obj)
    return res


class Document:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.owner_id = data.get('owner_id')
        self.title = data.get('title')
        self.size = data.get('size')
        self.ext = data.get('commands')
        self.url = data.get('url')
        self.date = data.get('date')
        self.type = data.get('type')
        self.access_key = data.get('access_key')

    def __str__(self):
        return f'doc{self.owner_id}_{self.id}'


class AudioMessage:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.owner_id = data.get('owner_id')
        self.duration = data.get('duration')
        self.waveform = data.get('waveform')
        self.link_ogg = data.get('link_ogg')
        self.link_mp3 = data.get('link_mp3')
        self.access_key = data.get('access_key')


class Sticker:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.product_id = data.get('product_id')
        self.sticker_id = data.get('sticker_id')
        self.images = [Size(image) for image in data.get('images')]
        self.images_with_background = [Size(image) for image in data.get('images_with_background')]


class Size:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.type = data.get('type')
        self.url = data.get('url')
        self.width = data.get('width')
        self.height = data.get('height')


class Photo:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.album_id = data.get('album_id')
        self.owner_id = data.get('owner_id')
        self.user_id = data.get('user_id')
        self.text = data.get('text')
        self.date = data.get('date')
        self.sizes = [Size(size) for size in data.get('sizes')] if data.get('sizes') else []
        self.width = data.get('width')
        self.height = data.get('height')

    def __str__(self):
        return f'photo{self.owner_id}_{self.id}'


class DeletedPhoto:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.owner_id = data.get('owner_id')
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.deleter_id = data.get('deleter_id')
        self.photo_id = data.get('photo_id')


class Audio:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.owner_id = data.get('owner_id')
        self.artist = data.get('artist')
        self.title = data.get('title')
        self.duration = data.get('duration')
        self.url = data.get('url')
        self.lyrics_id = data.get('lyrics_id')
        self.album_id = data.get('album_id')
        self.genre_id = data.get('genre_id')
        self.date = data.get('date')
        self.no_search = data.get('no_search')
        self.is_hq = data.get('is_hq')

    def __str__(self):
        return f'audio{self.owner_id}_{self.id}'


class Video:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.owner_id = data.get('owner_id')
        self.title = data.get('title')
        self.description = data.get('description')
        self.duration = data.get('duration')
        self.photo_130 = data.get('photo_130')
        self.photo_320 = data.get('photo_320')
        self.photo_640 = data.get('photo_640')
        self.photo_800 = data.get('photo_800')
        self.photo_1280 = data.get('photo_1280')
        self.first_frame_130 = data.get('first_frame_130')
        self.first_frame_320 = data.get('first_frame_320')
        self.first_frame_640 = data.get('first_frame_640')
        self.first_frame_800 = data.get('first_frame_800')
        self.first_frame_1280 = data.get('first_frame_1280')
        self.date = data.get('date')
        self.adding_date = data.get('adding_date')
        self.views = data.get('views')
        self.comments = data.get('comments')
        self.player = data.get('player')
        self.platform = data.get('platform')
        self.can_edit = data.get('can_edit')
        self.can_add = data.get('can_add')
        self.is_private = data.get('is_private')
        self.access_key = data.get('access_key')
        self.processing = data.get('processing')
        self.live = data.get('live')
        self.upcoming = data.get('upcoming')
        self.is_favorite = data.get('is_favorite')

    def __str__(self):
        return f'video{self.owner_id}_{self.id}'


class PollAnswer:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.text = data.get('text')
        self.votes = data.get('votes')
        self.rate = data.get('rate')


class Poll:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.owner_id = data.get('owner_id')
        self.created = data.get('created')
        self.question = data.get('question')
        self.votes = data.get('votes')
        answers = data.get('answers')
        self.answers = [PollAnswer(answer) for answer in answers]
        self.anonymous = data.get('anonymous')
        self.multiple = data.get('multiple')
        self.answer_ids = data.get('answer_ids')
        self.end_date = data.get('end_date')
        self.closed = data.get('closed')
        self.is_board = data.get('is_board')
        self.can_edit = data.get('can_edit')
        self.can_vote = data.get('can_vote')
        self.can_report = data.get('can_report')
        self.can_share = data.get('can_share')
        self.author_id = data.get('author_id')

    def __str__(self):
        return f'poll{self.owner_id}_{self.id}'


class Attachment:
    """Represents VK Attachment.

    You can get str(:class:`.Attachment`) to get string representation used by VK API or pass it to :meth:`.Bot.send_message`

    Attributes
    -----------
    owner_id: :class:`int`
        Id of attachment owner. Positive integer for users, negative for groups.
    id: :class:`int`
        Id of attachment itself. Positive integer.
    type: :class:`str`
        Type of an attachment. Can be value from :class:`.AttachmentType` enum.
    """
    def __init__(self, owner_id, id, type):
        self.id = id
        self.owner_id = owner_id
        self.type = type.value if isinstance(type, AttachmentType) else type

    def __str__(self):
        return f'{self.type}{self.owner_id}_{self.id}'
