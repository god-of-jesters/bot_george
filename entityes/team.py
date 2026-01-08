from entityes.user import User

class Team:
    def __init__(self, team_number: int, team_name: str = None, members: list = None):
        self.team_number = team_number
        self.team_name = team_name
        self.members = [user.user_id for user in members] if members else []