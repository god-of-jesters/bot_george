from dataclasses import dataclass
from datetime import datetime

class User:
    def __init__(self, user_id: int, fio: str = None, team_number: int = None, role: str = None, num_badge: int = None, reiting: int = None, balance: int = None):
        self.user_id = user_id
        self.fio = fio
        self.team_number = team_number
        self.role = role
        self.num_badge = num_badge
        self.reiting = reiting
        self.balance = balance
        self.date_registered = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def set_user_info(self, fio: str = None, team_number: int = None, role: str = None, num_badge: int = None, date_registered: str = None):
        self.fio = fio
        self.team_number = team_number
        self.role = role
        self.num_badge = num_badge
        self.date_registered = date_registered

@dataclass
class Role:
    name: str
    description: str
    acseess_to_complains: bool
    acseess_to_reports: bool
    acseess_to_files: bool
    acseess_change_to_teams: bool

ORGANIZER = Role(
    name="Организатор",
    description="Полный доступ ко всем функциям бота.",
    acseess_to_complains=True,
    acseess_to_reports=True,
    acseess_to_files=True,
    acseess_change_to_teams=False
)

RATING_TEAM = Role(
    name="Рейтинг Команды",
    description="Доступ к просмотру и управлению рейтингом команды.",
    acseess_to_complains=True,
    acseess_to_reports=True,
    acseess_to_files=False,
    acseess_change_to_teams=False
)


