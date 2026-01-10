from datetime import datetime

class Complaint:
    def __init__(self, complait_id: int = None, user_id: int = None, adresat: str = None, description: str = None, status: str = None, executing: str = None, files: list[int] = None):
        self.complait_id = complait_id
        self.user_id = user_id
        self.adresat = adresat
        self.description = description
        self.date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.date_resolved = None
        self.status = status
        self.executing = executing
        self.files = files if files is not None else []  # Список файлов, связанных с жалобой