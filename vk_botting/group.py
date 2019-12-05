from vk_botting.general import vk_request
from vk_botting.user import get_pages


async def get_groups(token, *gids):
    groups = await vk_request('groups.getById', token, group_ids=','.join(map(str, gids)))
    groups = groups.get('response')
    return [Group(group) for group in groups]


async def get_post(token, obj):
    post = Post(obj)
    post.author, post.creator, post.signer = await get_pages(token, post.from_id, post.created_by, post.signer_id)
    return post


async def get_wall_comment(token, obj):
    comment = WallComment(obj)
    comment.author, comment.reply_to = await get_pages(token, comment.from_id, comment.reply_to_user)
    return comment


async def get_deleted_wall_comment(token, obj):
    comment = DeletedWallComment(obj)
    comment.deleter, comment.owner = await get_pages(token, comment.deleter_id, comment.owner_id)
    return comment


async def get_board_comment(token, obj):
    comment = BoardComment(obj)
    author = await get_pages(token, comment.from_id)
    comment.author = author[0]
    return comment


async def get_deleted_board_comment(token, obj):
    comment = DeletedBoardComment(obj)
    topic_owner = await get_pages(token, comment.topic_owner_id)
    comment.topic_owner = topic_owner[0]
    return comment


async def get_video_comment(token, obj):
    comment = VideoComment(obj)
    comment.author, comment.reply_to = await get_pages(token, comment.from_id, comment.reply_to_user)
    return comment


async def get_deleted_video_comment(token, obj):
    comment = DeletedVideoComment(obj)
    comment.deleter, comment.owner, comment.author = await get_pages(token, comment.deleter_id, comment.owner_id, comment.user_id)
    return comment


async def get_photo_comment(token, obj):
    comment = PhotoComment(obj)
    comment.author, comment.reply_to = await get_pages(token, comment.from_id, comment.reply_to_user)
    return comment


async def get_deleted_photo_comment(token, obj):
    comment = DeletedPhotoComment(obj)
    comment.deleter, comment.owner, comment.author = await get_pages(token, comment.deleter_id, comment.owner_id, comment.user_id)
    return comment


async def get_market_comment(token, obj):
    comment = MarketComment(obj)
    comment.author, comment.reply_to = await get_pages(token, comment.from_id, comment.reply_to_user)
    return comment


async def get_deleted_market_comment(token, obj):
    comment = DeletedMarketComment(obj)
    comment.deleter, comment.owner, comment.author = await get_pages(token, comment.deleter_id, comment.owner_id, comment.user_id)
    return comment


async def get_poll_vote(token, obj):
    vote = PollVote(obj)
    vote.owner, vote.user = await get_pages(token, vote.owner_id, vote.user_id)
    return vote


async def get_officers_edit(token, obj):
    edit = OfficersEdit(obj)
    edit.admin, edit.author = await get_pages(token, edit.admin_id, edit.user_id)
    return edit


class Group:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.screen_name = data.get('screen_name')
        self.is_closed = data.get('is_closed')
        self.type = data.get('type')
        self.photo = {
            '50': data.get('photo_50'),
            '100': data.get('photo_100'),
            '200': data.get('photo_200')
        }


class Comments:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.count = data.get('count')
        self.can_post = data.get('can_post')
        self.groups_can_post = data.get('groups_can_post')
        self.can_close = data.get('can_close')
        self.can_open = data.get('can_open')


class Likes:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.count = data.get('count')
        self.user_likes = data.get('user_likes')
        self.can_like = data.get('can_like')
        self.can_publish = data.get('can_publish')


class Reposts:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.count = data.get('count')
        self.user_reposted = data.get('user_reposted')


class Views:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.count = data.get('count')


class Geo:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.type = data.get('type')
        self.coordinates = data.get('coordinates')
        self.place = data.get('place')


class Thread:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.count = data.get('count')
        self.items = data.get('items')
        self.can_post = data.get('can_post')
        self.show_reply_button = data.get('show_reply_button')
        self.groups_can_post = data.get('groups_can_post')


class WallComment:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.from_id = data.get('from_id')
        self.date = data.get('date')
        self.text = data.get('text')
        self.reply_to_user = data.get('reply_to_user')
        self.reply_to_comment = data.get('reply_to_comment')
        self.attachments = data.get('attachments')
        self.parents_stack = data.get('parents_stack')
        self.thread = Thread(data.get('thread'))
        self.post_id = data.get('post_id')
        self.post_owner_id = data.get('post_owner_id')


class DeletedWallComment:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.owner_id = data.get('owner_id')
        self.id = data.get('id')
        self.deleter_id = data.get('deleter_id')
        self.post_id = data.get('post_id')


class MarketComment:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.from_id = data.get('from_id')
        self.date = data.get('date')
        self.text = data.get('text')
        self.reply_to_user = data.get('reply_to_user')
        self.reply_to_comment = data.get('reply_to_comment')
        self.attachments = data.get('attachments')
        self.parents_stack = data.get('parents_stack')
        self.thread = Thread(data.get('thread'))
        self.market_owner_id = data.get('market_owner_id')
        self.item_id = data.get('item_id')


class DeletedMarketComment:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.owner_id = data.get('owner_id')
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.deleter_id = data.get('deleter_id')
        self.item_id = data.get('item_id')


class VideoComment:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.from_id = data.get('from_id')
        self.date = data.get('date')
        self.text = data.get('text')
        self.reply_to_user = data.get('reply_to_user')
        self.reply_to_comment = data.get('reply_to_comment')
        self.attachments = data.get('attachments')
        self.parents_stack = data.get('parents_stack')
        self.thread = Thread(data.get('thread'))
        self.video_id = data.get('video_id')
        self.video_owner_id = data.get('video_owner_id')


class DeletedVideoComment:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.owner_id = data.get('owner_id')
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.deleter_id = data.get('deleter_id')
        self.video_id = data.get('video_id')


class PhotoComment:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.from_id = data.get('from_id')
        self.date = data.get('date')
        self.text = data.get('text')
        self.reply_to_user = data.get('reply_to_user')
        self.reply_to_comment = data.get('reply_to_comment')
        self.attachments = data.get('attachments')
        self.parents_stack = data.get('parents_stack')
        self.thread = Thread(data.get('thread'))
        self.photo_id = data.get('photo_id')
        self.photo_owner_id = data.get('photo_owner_id')


class DeletedPhotoComment:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.owner_id = data.get('owner_id')
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.deleter_id = data.get('deleter_id')
        self.photo_id = data.get('photo_id')


class Post:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.from_id = data.get('from_id')
        self.owner_id = data.get('owner_id')
        self.date = data.get('date')
        self.marked_as_ads = data.get('marked_as_ads')
        self.post_type = data.get('post_type')
        self.text = data.get('text')
        self.can_pin = data.get('can_pin')
        self.can_edit = data.get('can_edit')
        self.created_by = data.get('created_by')
        self.can_delete = data.get('can_delete')
        self.comments = Comments(data.get('comments'))
        self.is_favorite = data.get('is_favorite')
        self.likes = Likes(data.get('likes'))
        self.reposts = Reposts(data.get('reposts'))
        self.views = Views(data.get('views'))
        self.attachments = data.get('attachments')
        self.geo = Geo(data.get('geo'))
        self.signer_id = data.get('signer_id')
        self.copy_history = data.get('copy_history')
        self.is_pinned = data.get('is_pinned')
        self.postponed_id = data.get('postponed_id')


class BoardComment:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.id = data.get('id')
        self.from_id = data.get('from_id')
        self.date = data.get('date')
        self.text = data.get('text')
        self.attachments = data.get('attachments')
        self.likes = Likes(data.get('likes'))
        self.topic_id = data.get('topic_id')
        self.topic_owner_id = data.get('topic_owner_id')


class DeletedBoardComment:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.topic_owner_id = data.get('topic_owner_id')
        self.topic_id = data.get('topic_id')
        self.id = data.get('id')


class PollVote:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.owner_id = data.get('owner_id')
        self.poll_id = data.get('poll_id')
        self.option_id = data.get('option_id')
        self.user_id = data.get('user_id')


class OfficersEdit:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.admin_id = data.get('admin_id')
        self.user_id = data.get('user_id')
        self.level_old = data.get('level_old')
        self.level_new = data.get('level_new')
