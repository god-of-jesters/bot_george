from datetime import datetime

class File:
    def __init__(self, id: int, tg_id: int, tg_file_id: str, complaint_id: int = None, file_name: str = None, mime_type: str = None, file_size: int = None, date_created: str = None):
        self.file_id = id
        self.tg_id = tg_id
        self.tg_file_id = tg_file_id
        self.complaint_id = complaint_id
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_size = file_size
        self.date_created = date_created or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
