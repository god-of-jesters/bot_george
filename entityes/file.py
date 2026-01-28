from datetime import datetime

class File:
    def __init__(self, id=None, tg_id=None, tg_file_id=None, complaint_id=None,
                 file_name=None, mime_type=None, file_size=None, date_created=None):
        self.id = id
        self.tg_id = tg_id
        self.tg_file_id = tg_file_id
        self.complaint_id = complaint_id
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_size = file_size
        self.date_created = date_created or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
