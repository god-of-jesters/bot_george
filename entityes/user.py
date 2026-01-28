from dataclasses import dataclass
from datetime import datetime

class User:
    def __init__(self, user_id: int, fio: str = None, team_number: int = None, role: str = None, badge_number: int = None, reiting: int = None, balance: int = None):
        self.user_id = user_id
        self.fio = fio
        self.team_number = team_number
        self.role = role
        self.badge_number = badge_number
        self.reiting = reiting
        self.balance = balance
        self.date_registered = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        
        return other.fio == self.fio and self.badge_number == other.badge_number
    
    def update(self, new_user: 'User'):
        self.fio = new_user.fio
        self.team_number = new_user.team_number
        self.role = new_user.role
        self.badge_number = new_user.badge_number
        self.reiting = new_user.reiting
        self.balance = new_user.balance