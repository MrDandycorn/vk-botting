from vk_botting.general import vk_request
from vk_botting.abstract import Messageable


async def get_own_page(token):
    from vk_botting.group import Group
    user = await vk_request('users.get', token)
    if not user.get('response'):
        group = await vk_request('groups.getById', token)
        return Group(group.get('response')[0])
    return User(user.get('response')[0])


async def get_users(token, *uids):
    users = await vk_request('users.get', token, user_ids=','.join(map(str, uids)))
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
