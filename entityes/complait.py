from datetime import datetime

class Complaint:
    def __init__(self, complait_id: int, user_id: int, title: str, description: str, date_created: str, status: str, files: list[int] = None):
        self.complait_id = complait_id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status = status
        self.files = files if files is not None else []  # Список файлов, связанных с жалобой