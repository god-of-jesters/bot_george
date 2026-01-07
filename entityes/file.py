class File:
    def __init__(self, id: str, tg_id: str, tg_file_id: int, file_name: str, mime_type: str, file_size: int, file_path: str, date_created: str = None):
        self.file_id = id
        self.file_tg_id = tg_id
        self.file_tg_file_id = tg_file_id
        self.file_name = file_name
        self.file_size = file_size
        self.file_path = file_path
        self.mime_type = mime_type
        self.date_created = date_created
