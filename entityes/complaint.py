from datetime import datetime

class Complaint:
    def __init__(self, complaint_id: int = None, user_id: int = None, adresat: int = None, violetion: str = None, description: str = None, status: str = None, execution: str = None, files: list[int] = None):
        self.complaint_id = complaint_id
        self.user_id = user_id
        self.adresat = adresat
        self.violetion = violetion
        self.description = description
        self.date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.date_resolved = None
        self.status = status
        self.execution = "new" or execution
        self.files = files if files is not None else []  # Список id файлов, связанных с жалобой
        self.video_count = 0
        self.photo_count = 0