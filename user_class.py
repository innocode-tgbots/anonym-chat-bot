__all__ = ['User']


class User:
    user_id: int
    name: str
    partner_id: int

    def __init__(self, user_id: int, name: str = None, partner_id: int = None):
        self.user_id = user_id
        self.name = name
        self.partner_id = partner_id
