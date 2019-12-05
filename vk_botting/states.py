async def get_state(token, obj):
    state = State(obj)
    return state


class State:

    def __init__(self, data):
        self._unpack(data)

    def _unpack(self, data):
        self.state = data.get('state')
        self.from_id = data.get('from_id')
        self.to_id = data.get('to_id')
