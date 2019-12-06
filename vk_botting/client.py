import asyncio
import sys
import traceback
import aiohttp
import enum
from random import randint

from vk_botting.general import vk_request
from vk_botting.user import get_own_page, get_pages, get_users, get_blocked_user, get_unblocked_user, User
from vk_botting.group import get_post, get_board_comment, get_market_comment, get_photo_comment, get_video_comment, get_wall_comment, get_deleted_photo_comment,\
    get_deleted_video_comment, get_deleted_board_comment, get_deleted_market_comment, get_deleted_wall_comment, get_officers_edit, get_poll_vote, get_groups, Group
from vk_botting.attachments import get_photo, get_video, get_audio
from vk_botting.message import build_msg, build_user_msg
from vk_botting.states import get_state
from vk_botting.exceptions import VKApiError, LoginError


class UserMessageFlags(enum.IntFlag):
    Unread = 1,
    Outbox = 2,
    Replied = 4,
    Important = 8,
    Chat = 16,
    Friends = 32,
    Spam = 64,
    Deleted = 128,
    Fixed = 256,
    Media = 512,
    Hidden = 65536,
    DeleteForAll = 131072,
    NotDelivered = 262144


class _ClientEventTask(asyncio.Task):
    def __init__(self, original_coro, event_name, coro, *, loop):
        super().__init__(coro, loop=loop)
        self.__event_name = event_name
        self.__original_coro = original_coro

    def __repr__(self):
        info = [
            ('state', self._state.lower()),
            ('event', self.__event_name),
            ('coro', repr(self.__original_coro)),
        ]
        if self._exception is not None:
            info.append(('exception', repr(self._exception)))
        return '<ClientEventTask {}>'.format(' '.join('%s=%s' % t for t in info))


class Client:

    def __init__(self, **kwargs):
        self.v = kwargs.get('v', '5.999')
        self.force = kwargs.get('force', False)
        self.loop = asyncio.get_event_loop()
        self.user = None
        self.group = None
        self.key = None
        self.server = None
        self.old_longpoll = kwargs.get('old_longpoll', False)
        self._listeners = {}
        timeout = aiohttp.ClientTimeout(total=100, connect=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        self._implemented_events = ['message_new', 'message_reply', 'message_allow', 'message_deny', 'message_edit', 'message_typing_state', 'photo_new', 'audio_new', 'video_new', 'wall_reply_new', 'wall_reply_edit', 'wall_reply_delete', 'wall_reply_restore', 'wall_post_new', 'wall_repost', 'board_post_new', 'board_post_edit', 'board_post_restore', 'board_post_delete', 'photo_comment_new', 'photo_comment_edit', 'photo_comment_delete', 'photo_comment_restore', 'video_comment_new', 'video_comment_edit', 'video_comment_delete', 'video_comment_restore', 'market_comment_new', 'market_comment_edit', 'market_comment_delete', 'market_comment_restore', 'poll_vote_new', 'group_join', 'group_leave', 'group_change_settings', 'group_change_photo', 'group_officers_edit', 'user_block', 'user_unblock']

    def Payload(self, **kwargs):
        kwargs['access_token'] = self.token
        kwargs['v'] = self.v
        return kwargs

    class botCommandException(Exception):
        pass

    def wait_for(self, event, *, check=None, timeout=None):
        future = self.loop.create_future()
        if check is None:
            def _check(*args):
                return True
            check = _check

        ev = event.lower()
        try:
            listeners = self._listeners[ev]
        except KeyError:
            listeners = []
            self._listeners[ev] = listeners

        listeners.append((future, check))
        return asyncio.wait_for(future, timeout, loop=self.loop)

    async def general_request(self, url, post=False, **params):
        for param in list(params):
            if params[param] is None:
                params.pop(param)
            elif not isinstance(params[param], (str, int)):
                params[param] = str(params[param])
            elif isinstance(params[param], bool):
                params[param] = str(params[param])
        for tries in range(5):
            try:
                req = self.session.post(url, data=params) if post else self.session.get(url, params=params)
                async with req as r:
                    if r.content_type == 'application/json':
                        return await r.json()
                    return await r.text()
            except Exception as e:
                print(f'Got exception in request: {e}\nRetrying in {tries*2+1} seconds', file=sys.stderr)
                await asyncio.sleep(tries*2+1)

    async def vk_request(self, method, **kwargs):
        res = await self.general_request(f'https://api.vk.com/method/{method}', **self.Payload(**kwargs))
        error = res.get('error', None)
        if error and error['error_code'] == 6:
            await asyncio.sleep(1)
            return await self.vk_request(method, **kwargs)
        return res

    async def enable_longpoll(self):
        events = dict([(event, 1) for event in self._implemented_events])
        res = await self.vk_request('groups.setLongPollSettings', group_id=self.group.id, enabled=1, api_version='5.103', **events)
        return res

    async def get_user_longpoll(self):
        res = await self.vk_request('messages.getLongPollServer', group_id=self.group.id, lp_version=3)
        error = res.get('error', None)
        if error and error['error_code'] == 15:
            raise LoginError('User has no access to messages API. Try generating token with vk_botting.auth methods')
        elif error and error['error_code'] == 100:
            if self.force:
                await self.enable_longpoll()
                return await self.get_longpoll_server()
            raise VKApiError('Longpoll is disabled for this group. Enable longpoll or try force mode')
        elif error:
            raise VKApiError(f'[{error["error_code"]}]{error["error_msg"]}')
        self.key = res['response']['key']
        server = res['response']['server'].replace(r'\/', '/')
        self.server = f'https://{server}'
        ts = res['response']['ts']
        return ts

    async def get_longpoll_server(self):
        res = await self.vk_request('groups.getLongPollServer', group_id=self.group.id)
        error = res.get('error', None)
        if error and error['error_code'] == 100:
            if self.force:
                await self.enable_longpoll()
                return await self.get_longpoll_server()
            raise VKApiError('Longpoll is disabled for this group. Enable longpoll or try force mode')
        elif error:
            raise VKApiError(f'[{error["error_code"]}]{error["error_msg"]}')
        self.key = res['response']['key']
        self.server = res['response']['server'].replace(r'\/', '/')
        ts = res['response']['ts']
        return ts

    async def longpoll(self, ts):
        payload = {'key': self.key,
                   'act': 'a_check',
                   'ts': ts,
                   'wait': '10'}
        if not self.is_group:
            payload['mode'] = 10
        try:
            res = await self.general_request(self.server, **payload)
        except asyncio.TimeoutError:
            return ts, []
        if 'ts' not in res.keys() or 'failed' in res.keys():
            ts = await self.get_longpoll_server()
        else:
            ts = res['ts']
        updates = res.get('updates', [])
        return ts, updates

    async def handle_update(self, update):
        t = update['type']
        if t == 'message_new':
            obj = update['object'] if self.old_longpoll else update['object']['message']
            msg = await build_msg(obj, self)
            return self.dispatch(t, msg)
        elif t == 'message_reply' and 'on_message_reply' in self.extra_events:
            obj = update['object']
            msg = await build_msg(obj, self)
            return self.dispatch(t, msg)
        elif t == 'message_edit' and 'on_message_edit' in self.extra_events:
            obj = update['object']
            msg = await build_msg(obj, self)
            return self.dispatch(t, msg)
        elif t == 'message_typing_state' and 'on_message_typing_state' in self.extra_events:
            obj = update['object']
            state = await get_state(self.token, obj)
            return self.dispatch(t, state)
        elif t in ['message_allow', 'message_deny'] and any(event in self.extra_events for event in ['on_message_allow', 'on_message_deny']):
            obj = update['object']
            user = await get_pages(self.token, obj)
            return self.dispatch(t, user[0])
        elif t == 'photo_new' and 'on_photo_new' in self.extra_events:
            obj = update['object']
            photo = await get_photo(self.token, obj)
            return self.dispatch(t, photo)
        elif t in ['photo_comment_new', 'photo_comment_edit', 'photo_comment_restore'] and any(event in self.extra_events for event in ['on_photo_comment_new', 'on_photo_comment_edit', 'on_photo_comment_restore']):
            obj = update['object']
            comment = await get_photo_comment(self.token, obj)
            return self.dispatch(t, comment)
        elif t == 'photo_comment_delete' and 'on_photo_comment_delete' in self.extra_events:
            obj = update['object']
            deleted = await get_deleted_photo_comment(self.token, obj)
            return self.dispatch(t, deleted)
        elif t == 'audio_new' and 'on_audio_new' in self.extra_events:
            obj = update['object']
            audio = await get_audio(self.token, obj)
            return self.dispatch(t, audio)
        elif t == 'video_new' and 'on_video_new' in self.extra_events:
            obj = update['object']
            video = await get_video(self.token, obj)
            return self.dispatch(t, video)
        elif t in ['video_comment_new', 'video_comment_edit', 'video_comment_restore'] and any(event in self.extra_events for event in ['on_video_comment_new', 'on_video_comment_edit', 'on_video_comment_restore']):
            obj = update['object']
            comment = get_video_comment(self.token, obj)
            return self.dispatch(t, comment)
        elif t == 'video_comment_delete' and 'on_video_comment_delete' in self.extra_events:
            obj = update['object']
            deleted = await get_deleted_video_comment(self.token, obj)
            return self.dispatch(t, deleted)
        elif t in ['wall_post_new', 'wall_repost'] and any(event in self.extra_events for event in ['on_wall_post_new', 'on_wall_repost']):
            obj = update['object']
            post = await get_post(self.token, obj)
            return self.dispatch(t, post)
        elif t in ['wall_reply_new', 'wall_reply_edit', 'wall_reply_restore'] and any(event in self.extra_events for event in ['on_wall_reply_new', 'on_wall_reply_edit', 'on_wall_reply_restore']):
            obj = update['object']
            comment = await get_wall_comment(self.token, obj)
            return self.dispatch(t, comment)
        elif t == 'wall_reply_delete' and 'on_wall_reply_delete' in self.extra_events:
            obj = update['object']
            deleted = await get_deleted_wall_comment(self.token, obj)
            return self.dispatch(t, deleted)
        elif t in ['board_post_new', 'board_post_edit', 'board_post_restore'] and any(event in self.extra_events for event in ['on_board_post_new', 'on_board_post_edit', 'on_board_post_restore']):
            obj = update['object']
            comment = await get_board_comment(self.token, obj)
            return self.dispatch(t, comment)
        elif t == 'board_post_delete' and 'on_board_post_delete' in self.extra_events:
            obj = update['object']
            deleted = await get_deleted_board_comment(self.token, obj)
            return self.dispatch(t, deleted)
        elif t in ['market_comment_new', 'market_comment_edit', 'market_comment_restore'] and any(event in self.extra_events for event in ['on_market_comment_new', 'on_market_comment_edit', 'on_market_comment_restore']):
            obj = update['object']
            comment = await get_market_comment(self.token, obj)
            return self.dispatch(t, comment)
        elif t == 'market_comment_delete' and 'on_market_comment_delete' in self.extra_events:
            obj = update['object']
            deleted = await get_deleted_market_comment(self.token, obj)
            return self.dispatch(t, deleted)
        elif t == 'group_leave' and 'on_group_leave' in self.extra_events:
            obj = update['object']
            user = await get_pages(self.token, obj['user_id'])
            return self.dispatch(t, (user[0], obj['self']))
        elif t == 'group_join' and 'on_group_join' in self.extra_events:
            obj = update['object']
            user = await get_pages(self.token, obj['user_id'])
            return self.dispatch(t, (user[0], obj['join_type']))
        elif t == 'user_block' and 'on_user_block' in self.extra_events:
            obj = update['object']
            blocked = await get_blocked_user(self.token, obj)
            return self.dispatch(t, blocked)
        elif t == 'user_unblock' and 'on_user_unblock' in self.extra_events:
            obj = update['object']
            unblocked = await get_unblocked_user(self.token, obj)
            return self.dispatch(t, unblocked)
        elif t == 'poll_vote_new' and 'on_poll_vote_new' in self.extra_events:
            obj = update['object']
            vote = await get_poll_vote(self.token, obj)
            return self.dispatch(t, vote)
        elif t == 'group_officers_edit' and 'on_group_officers_edit' in self.extra_events:
            obj = update['object']
            edit = await get_officers_edit(self.token, obj)
            return self.dispatch(t, edit)
        elif 'on_unknown' in self.extra_events:
            return self.dispatch('unknown', update)

    async def handle_user_update(self, update):
        t = update.pop(0)
        if t == 4 and 'on_message_new' in self.extra_events:
            data = {
                'id': update.pop(0),
                'flags': UserMessageFlags(update.pop(0)),
                'peer_id': update.pop(0),
                'date': update.pop(0),
                'text': update.pop(1),
                'attachments': update.pop(1)
            }
            msg = await build_user_msg(data, self)
            return self.dispatch('message_new', msg)
        elif 'on_unknown' in self.extra_events:
            return self.dispatch('unknown', update)

    def dispatch(self, event, *args, **kwargs):
        method = 'on_' + event
        listeners = self._listeners.get(event)
        if listeners:
            removed = []
            for i, (future, condition) in enumerate(listeners):
                if future.cancelled():
                    removed.append(i)
                    continue

                try:
                    result = condition(*args)
                except Exception as exc:
                    future.set_exception(exc)
                    removed.append(i)
                else:
                    if result:
                        if len(args) == 0:
                            future.set_result(None)
                        elif len(args) == 1:
                            future.set_result(args[0])
                        else:
                            future.set_result(args)
                        removed.append(i)

            if len(removed) == len(listeners):
                self._listeners.pop(event)
            else:
                for idx in reversed(removed):
                    del listeners[idx]

        try:
            coro = getattr(self, method)
        except AttributeError:
            pass
        else:
            self._schedule_event(coro, method, *args, **kwargs)

    async def on_error(self, event_method, *args, **kwargs):
        print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
        traceback.print_exc()

    async def _run_event(self, coro, event_name, *args, **kwargs):
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def _schedule_event(self, coro, event_name, *args, **kwargs):
        wrapped = self._run_event(coro, event_name, *args, **kwargs)
        return _ClientEventTask(original_coro=coro, event_name=event_name, coro=wrapped, loop=self.loop)

    async def get_user(self, uid):
        user = await get_users(self.token, uid)
        if user:
            return user[0]
        return None

    async def get_group(self, gid):
        group = await get_groups(self.token, gid)
        if group:
            return group[0]
        return None

    async def send_message(self, peer_id=None, message=None, *, attachment=None, sticker_id=None, keyboard=None, reply_to=None, forward_messages=None):
        params = {'group_id': self.group.id, 'random_id': randint(-2 ** 63, 2 ** 63 - 1), 'peer_id': peer_id, 'message': message, 'attachment': attachment,
                  'reply_to': reply_to, 'forward_messages': forward_messages, 'sticker_id': sticker_id, 'keyboard': keyboard}
        res = await vk_request('messages.send', self.token, **params)
        if 'error' in res.keys():
            raise VKApiError('[{error_code}] {error_msg}'.format(**res['error']))
        params['id'] = res['response']
        params['from_id'] = -self.group.id
        return await build_msg(params, self)

    async def _run(self, owner_id):
        if owner_id and owner_id.__class__ is not int:
            raise TypeError(f'Owner_id must be positive integer, not {owner_id.__class__.__name__}')
        if owner_id and owner_id < 0:
            raise VKApiError(f'Owner_id must be positive integer')
        user = await get_own_page(self.token)
        if user.__class__ is User:
            self.is_group = False
            self.group = Group({})
            self.user = user
            ts = await self.get_user_longpoll()
            self.dispatch('ready')
            updates = []
            while True:
                try:
                    lp = self.loop.create_task(self.longpoll(ts))
                    for update in updates:
                        self.loop.create_task(self.handle_user_update(update))
                    ts, updates = await lp
                except Exception as e:
                    print(f'Ignoring exception in longpoll cycle:\n{e}', file=sys.stderr)
                    ts = await self.get_longpoll_server()
        else:
            self.is_group = True
            self.group = user
            self.user = User({})
            if self.is_group and owner_id:
                raise VKApiError('Owner_id passed together with group access_token')
            ts = await self.get_longpoll_server()
            self.dispatch('ready')
            updates = []
            while True:
                try:
                    lp = self.loop.create_task(self.longpoll(ts))
                    for update in updates:
                        self.loop.create_task(self.handle_update(update))
                    ts, updates = await lp
                except Exception as e:
                    print(f'Ignoring exception in longpoll cycle:\n{e}', file=sys.stderr)
                    ts = await self.get_longpoll_server()

    def run(self, token, owner_id=None):
        self.token = token
        self.loop.create_task(self._run(owner_id))
        self.loop.run_forever()
