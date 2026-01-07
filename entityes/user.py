class User:
    def __init__(self, user_id: int, fio: str = None, team_number: int = None, role: str = None, num_badge: int = None, date_registered: str = None):
        self.user_id = user_id
        self.fio = fio
        self.team_number = team_number
        self.role = role
        self.num_badge = num_badge
        self.date_registered = date_registered

    def set_user_info(self, fio: str = None, team_number: int = None, role: str = None, num_badge: int = None, date_registered: str = None):
        self.fio = fio
        self.team_number = team_number
        self.role = role
        self.num_badge = num_badge
        self.date_registered = date_registered
