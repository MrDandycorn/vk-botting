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

from vk_botting.general import vk_request
from vk_botting.abstract import Messageable


async def get_own_page(token):
    from vk_botting.group import Group
    user = await vk_request('users.get', token)
    if not user.get('response'):
        group = await vk_request('groups.getById', token)
        return Group(group.get('response')[0])
    return User(user.get('response')[0])


async def get_users(token, *uids, fields=None, name_case=None):
    if fields is None:
        fields = ['photo_id', ' verified', ' sex', ' bdate', ' city', ' country', ' home_town', ' has_photo', ' photo_50', ' photo_100', ' photo_200_orig', ' photo_200',
                  ' photo_400_orig', ' photo_max', ' photo_max_orig', ' online', ' domain', ' has_mobile', ' contacts', ' site', ' education', ' universities', ' schools',
                  ' status', ' last_seen', ' followers_count', ' common_count', ' occupation', ' nickname', ' relatives', ' relation', ' personal', ' connections', ' exports',
                  ' activities', ' interests', ' music', ' movies', ' tv', ' books', ' games', ' about', ' quotes', ' can_post', ' can_see_all_posts', ' can_see_audio',
                  ' can_write_private_message', ' can_send_friend_request', ' is_favorite', ' is_hidden_from_feed', ' timezone', ' screen_name', ' maiden_name', ' crop_photo',
                  ' is_friend', ' friend_status', ' career', ' military', ' blacklisted', ' blacklisted_by_me', ' can_be_invited_group']
    if name_case is None:
        name_case = 'nom'
    users = await vk_request('users.get', token, user_ids=','.join(map(str, uids)), fields=fields, name_case=name_case)
    users = users.get('response')
    return [User(user) for user in users]


async def get_pages(token, *ids):
    from vk_botting.group import get_groups
    g = []
    u = []
    for pid in ids:
        if pid < 0:
            g.append(-pid)
        else:
            u.append(pid)
    users = await get_users(token, *u)
    groups = await get_groups(token, *g)
    res = []
    for pid in ids:
        if pid < 0:
            for group in groups:
                if -pid == group.id:
                    res.append(group)
                    break
            else:
                res.append(None)
        else:
            for user in users:
                if pid == user.id:
                    res.append(user)
                    break
            else:
                res.append(None)
    return res


async def get_blocked_user(token, obj):
    blocked = BlockedUser(obj)
    blocked.admin, blocked.user = await get_pages(token, blocked.admin_id, blocked.user_id)
    return blocked


async def get_unblocked_user(token, obj):
    unblocked = UnblockedUser(obj)
    unblocked.admin = await get_pages(token, unblocked.admin_id, unblocked.user_id)
    return unblocked


class User(Messageable):

    async def _get_conversation(self):
        return self.id

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.first_name = data.get('first_name')
        self.last_name = data.get('last_name')
        self.is_closed = data.get('is_closed')
        self.can_access_closed = data.get('can_access_closed')
        self.photo_id = data.get('photo_id')
        self.verified = data.get('verified')
        self.sex = data.get('sex')
        self.bdate = data.get('bdate')
        self.city = data.get('city')
        self.country = data.get('country')
        self.home_town = data.get('home_town')
        self.has_photo = data.get('has_photo')
        self.photo_50 = data.get('photo_50')
        self.photo_100 = data.get('photo_100')
        self.photo_200_orig = data.get('photo_200_orig')
        self.photo_200 = data.get('photo_200')
        self.photo_400_orig = data.get('photo_400_orig')
        self.photo_max = data.get('photo_max')
        self.photo_max_orig = data.get('photo_max_orig')
        self.online = data.get('online')
        self.domain = data.get('domain')
        self.has_mobile = data.get('has_mobile')
        self.contacts = data.get('contacts')
        self.site = data.get('site')
        self.education = data.get('education')
        self.universities = data.get('universities')
        self.schools = data.get('schools')
        self.status = data.get('status')
        self.last_seen = data.get('last_seen')
        self.followers_count = data.get('followers_count')
        self.common_count = data.get('common_count')
        self.occupation = data.get('occupation')
        self.nickname = data.get('nickname')
        self.relatives = data.get('relatives')
        self.relation = data.get('relation')
        self.personal = data.get('personal')
        self.connections = data.get('connections')
        self.exports = data.get('exports')
        self.activities = data.get('activities')
        self.interests = data.get('interests')
        self.music = data.get('music')
        self.movies = data.get('movies')
        self.tv = data.get('tv')
        self.books = data.get('books')
        self.games = data.get('games')
        self.about = data.get('about')
        self.quotes = data.get('quotes')
        self.can_post = data.get('can_post')
        self.can_see_all_posts = data.get('can_see_all_posts')
        self.can_see_audio = data.get('can_see_audio')
        self.can_write_private_message = data.get('can_write_private_message')
        self.can_send_friend_request = data.get('can_send_friend_request')
        self.is_favorite = data.get('is_favorite')
        self.is_hidden_from_feed = data.get('is_hidden_from_feed')
        self.timezone = data.get('timezone')
        self.screen_name = data.get('screen_name')
        self.maiden_name = data.get('maiden_name')
        self.crop_photo = data.get('crop_photo')
        self.is_friend = data.get('is_friend')
        self.friend_status = data.get('friend_status')
        self.career = data.get('career')
        self.military = data.get('military')
        self.blacklisted = data.get('blacklisted')
        self.blacklisted_by_me = data.get('blacklisted_by_me')
        self.can_be_invited_group = data.get('can_be_invited_group')


class BlockedUser:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.admin_id = data.get('admin_id')
        self.user_id = data.get('user_id')
        self.unblock_date = data.get('unblock_date')
        self.reason = data.get('reason')
        self.comment = data.get('comment')


class UnblockedUser:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.admin_id = data.get('admin_id')
        self.user_id = data.get('user_id')
        self.by_end_date = data.get('by_end_date')
