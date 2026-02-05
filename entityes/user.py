from datetime import datetime

class User:
    def __init__(
        self,
        tg_id: int,
        username: str | None = None,
        fio: str = None,
        team_number: int = None,
        role: str = None,
        badge_number: int = None,
        reiting: int = None,
        balance: int = None,
        gender: str | None = None,
        date_registered: str = None,
    ):
        self.tg_id = tg_id
        self.username = username
        self.fio = fio
        self.team_number = team_number
        self.role = role
        self.badge_number = badge_number
        self.reiting = reiting
        self.balance = balance
        self.gender = gender
        self.date_registered = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if date_registered is None
            else date_registered
        )

    def update(self, new_user: "User"):
        self.username = new_user.username
        self.fio = new_user.fio
        self.team_number = new_user.team_number
        self.role = new_user.role
        self.badge_number = new_user.badge_number
        self.reiting = new_user.reiting
        self.balance = new_user.balance
        self.gender = new_user.gender
